;; Read-only bridge to the preserved gd-edit decoder and seeded item-stat engine.
(require '[clojure.data.json :as json] '[clojure.java.io :as io])
(def req (json/read-str (slurp (first *command-line-args*))))
(def out (second *command-line-args*))
(case (get req "operation")
 "decode"
 (do
  (require '[gd-edit.io.gdc :as gdc] '[gd-edit.io.stash :as stash])
  (let [load-char (resolve 'gd-edit.io.gdc/load-character-file)
        load-stash (resolve 'gd-edit.io.stash/load-stash-file)]
   (spit out (json/write-str
    {:characters (mapv (fn [p] {:path p :data (load-char p)}) (get req "characters"))
     :stash (when-let [p (get req "stash")] (load-stash p))}))))
 "roll"
 (do
  (require '[gd-edit.item-stats :as stats] '[gd-edit.globals :as g]
           '[gd-edit.item-summary :as summary])
  (let [idx (into {} (for [[p r] (get req "records")] [p (assoc r :recordname p)]))
        gidx (resolve 'gd-edit.globals/db-index)
        gdb (resolve 'gd-edit.globals/db)
        gall (resolve 'gd-edit.globals/db-and-index)
        roll (resolve 'gd-edit.item-stats/rolled-stats)
        completion (resolve 'gd-edit.item-stats/completion-bonus)
        requirements (resolve 'gd-edit.item-summary/record-requirements)]
   (reset! @gidx idx) (reset! @gdb (vals idx))
   (reset! @gall {:db (vals idx) :index idx})
   (spit out (json/write-str
    (mapv (fn [entry]
     (let [item (into {} (map (fn [[k v]] [(keyword k) v]) (get entry "save")))
           base (get idx (:basename item))]
      {:key (get entry "key") :rolled (roll item)
       :worn-rolled (roll (if (= "ItemArtifact" (get base "Class")) (assoc item :modifier-name "") item))
       :completion (:values (completion item))
       :requirements (try (requirements base) (catch Throwable e {:error (str e)}))})) (get req "items"))))))
 "baseline"
 (do
  (require '[gd-edit.globals :as g] '[gd-edit.commands.export :as export])
  (let [idx (with-open [r (java.io.InputStreamReader. (java.util.zip.GZIPInputStream. (java.io.FileInputStream. (get req "database"))) "UTF-8")]
              (into {} (for [[p r] (json/read r)] [p (assoc r :recordname p)])))
        m (json/read-str (slurp (get req "character")) :key-fn keyword)
        loc (json/read-str (slurp (get req "localization")))]
   (reset! @(resolve 'gd-edit.globals/db-index) idx)
   (reset! @(resolve 'gd-edit.globals/db) (vals idx))
   (reset! @(resolve 'gd-edit.globals/db-and-index) {:db (vals idx) :index idx})
   (reset! @(resolve 'gd-edit.globals/localization-table) loc)
   (spit out (json/write-str ((resolve 'gd-edit.commands.export/character-json) m)))))
 (throw (Exception. "Unknown bridge operation")))
(shutdown-agents)
