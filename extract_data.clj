;; Read-only source extractor. Run through refresh_data.py; never writes saves.
(require '[gd-edit.io.arz :as arz] '[gd-edit.io.arc :as arc] '[gd-edit.io.gdc :as gdc]
 '[gd-edit.io.stash :as stash] '[gd-edit.globals :as g] '[gd-edit.db-utils :as dbu]
 '[gd-edit.item-stats :as stats] '[gd-edit.item-summary :as summary]
 '[gd-edit.commands.export :as ex] '[gd-edit.resistances :as res]
 '[clojure.java.io :as io] '[clojure.data.json :as json])
(import '[java.util.zip GZIPOutputStream] '[java.io FileOutputStream OutputStreamWriter])
(def game (nth *command-line-args* 0))
(def saves (nth *command-line-args* 1))
(def out (nth *command-line-args* 2))
(def selected-character (nth *command-line-args* 3 "Mal"))
(.mkdirs (io/file out))
(def tiers (filter #(.exists (io/file game % "resources/Text_EN.arc")) ["" "gdx1" "gdx2" "gdx3"]))
(def loc (apply merge (map #(arc/load-localization-table (str (io/file game % "resources/Text_EN.arc"))) tiers)))
(reset! g/localization-table loc)
(def idx (apply merge (for [t tiers :let [n (if (= t "") "database" (.toUpperCase t))]]
 (into {} (map (juxt :recordname identity) (arz/load-game-db (str (io/file game t "database" (str n ".arz"))) loc))))))
(reset! g/db (vals idx)) (reset! g/db-index idx) (reset! g/db-and-index {:db (vals idx) :index idx})
(assert (stats/available?) "Rolled-stat engine is unavailable; extraction cannot produce numeric inputs")
(def chars (mapv #(gdc/load-character-file (.getPath %)) (filter #(= "player.gdc" (.getName %)) (file-seq (io/file saves "main")))))
(def mal (first (filter #(= selected-character (:character-name %)) chars)))
(assert mal (str "No character named " selected-character " in supplied save/main directory"))
(def result (atom []))
(defn scan [x owner location]
 (cond
  (and (map? x) (not-empty (:basename x)))
  (let [base (get idx (:basename x))]
   (swap! result conj {:id (format "GD%04d" (inc (count @result))) :owner owner :location location :save x
    :name (dbu/item-name x (dbu/db-and-index))
    :records (mapv #(get idx (get x %)) [:basename :prefix-name :suffix-name :modifier-name :relic-name :augment-name :relic-bonus :ascended-name])
    :rolled (stats/rolled-stats x)
    :worn-rolled (stats/rolled-stats (if (= "ItemArtifact" (get base "Class")) (assoc x :modifier-name "") x))
    :completion (:values (stats/completion-bonus x))
    :requirements (try (summary/record-requirements base) (catch Throwable e {:error (str e)}))}))
  (map? x) (doseq [[k v] x :when (and (coll? v) (not= k :meta-block-list))] (scan v owner (str location "/" (name k))))
  (sequential? x) (doseq [[i v] (map-indexed vector x)] (scan v owner (str location "/" i)))))
(doseq [c chars] (scan c (:character-name c) ""))
(scan (stash/load-stash-file (str (io/file saves "transfer.gst"))) "Shared Stash" "")
(defn write-json [n v] (spit (io/file out n) (json/write-str v)))
(with-open [w (OutputStreamWriter. (GZIPOutputStream. (FileOutputStream. (str (io/file out "database.json.gz")))) "UTF-8")] (json/write idx w))
(write-json "localization.json" loc) (write-json "mal.json" mal) (write-json "catalog.json" @result)
(write-json "baseline.json" (ex/character-json mal)) (write-json "penalties.json" (res/penalties (res/difficulty mal)))
(def formulas (distinct (re-seq #"records/[a-zA-Z0-9_/.-]+\.dbr" (slurp (io/file saves "formulas.gst")))))
(write-json "recipes.json" (mapv (fn [p] (let [r (get idx p)] {:record p :definition r :result (get idx (get r "artifactName"))})) formulas))
(println "Extracted" (count @result) "item entries, difficulty" (res/difficulty mal) "roll engine" (stats/available?))
(shutdown-agents)
