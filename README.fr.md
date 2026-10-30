# Droneload : détection de marqueurs ArUco en temps réel

[English](README.md) | **Français**

Ce programme détecte des marqueurs ArUco à partir d'une caméra ou d'une vidéo, leur attribue un label et enregistre leur position dans l'image. Il a été écrit pour le RubikPi 3 (Qualcomm QCS6490), mais il fonctionne sur toute machine équipée d'OpenCV.

Il fournit le centre de chaque marqueur, en pixels. Il n'estime ni la pose ni la distance, et n'envoie rien au contrôleur de vol.

## État du projet

| Élément | État |
|---------|------|
| Détection, labels et enregistrement | Testés sur PC, sur des images générées et réelles |
| Caméra CSI du RubikPi | Non testée sur la carte ; le pipeline devra peut-être être adapté |
| Matériel | Pas encore choisi |
| Marqueurs du projet (`DICT_4X4_50`) | Non testés sur des images réelles |

Sur les images de test Shadow-ArUco, le détecteur a trouvé 56 % des marqueurs annotés, et 27 % de ses détections ne correspondaient à aucune annotation. Ces images utilisent un autre dictionnaire, si bien que ces chiffres ne valent pas forcément pour les marqueurs du projet. Le travail restant figure dans `TODO.md`.

## Démarrage rapide

Il suffit d'un PC avec Python 3. Toutes les commandes se lancent depuis la racine du dépôt.

```bash
pip install opencv-contrib-python
python3 -m testing.make_test_video          # aucune caméra nécessaire
python3 -m droneload.vision --source test_markers.mp4
```

Les résultats se trouvent dans `detections.csv` et `aruco_debug.jpg`.

## Utilisation

```bash
python3 -m droneload.vision [--source SOURCE] [--dict DICTIONNAIRE]
```

Par défaut, `--source` vaut `0`, soit la première webcam. Valeurs possibles :

| Valeur | Source |
|--------|--------|
| `0`, `1`, ... | Webcam ou autre caméra |
| `video.mp4` | Fichier vidéo |
| `"frames/%03d.jpg"` | Séquence d'images |
| Pipeline GStreamer | Nécessite OpenCV compilé avec GStreamer |
| `rubikpi-csi` | Caméra CSI du RubikPi |
| `picamera` | Caméra du Raspberry Pi, nécessite `picamera2` |

`--dict` prend le nom d'un dictionnaire `cv2.aruco` et vaut `DICT_4X4_50` par défaut.

Avec une vidéo ou des images, le programme s'arrête à la dernière image. Avec une source en direct, appuyez sur Ctrl+C pour l'arrêter.

## Fonctionnement

1. Lecture d'une image depuis la source.
2. Conversion en niveaux de gris, puis rehaussement du contraste par CLAHE, qui améliore la détection en faible luminosité.
3. Détection des marqueurs, en écartant ceux dont un côté mesure moins de 10 pixels (`MIN_SIDE_PX` dans `detect.py`).
4. Association de chaque ID à un label.
5. Enregistrement de chaque ID au plus une fois par seconde (`WRITE_COOLDOWN_MS`), pour limiter la taille du CSV. Cette limite suit le temps réel : une vidéo traitée plus vite que sa durée produit donc moins de lignes.

Pour être détectés, les marqueurs doivent être entourés d'une bordure blanche.

### Labels des marqueurs

Les labels sont définis dans `ARUCO_LABELS`, dans `detect.py`. Les autres ID apparaissent sous la forme `unknown_N`.

| ID | Label |
|----|-------|
| 0 | `zone_de_decollage` |
| 1 | `robot` |
| 2-3 | `align` |
| 4-11 | `fenetre_facile_*` (recto/verso, droite/gauche, haut/bas) |
| 12-15 | `fenetre_difficile_*` (recto/verso, haut/bas) |

### Sorties

**Terminal, toutes les 2 secondes :**
```
[14:32:01] detect=3.2ms
  ID= 0  label=zone_de_decollage                         center=(640.0,360.0)
  ID= 4  label=fenetre_facile_recto_droite_bas           center=(213.5,180.2)
```

**`detections.csv` :**
```
timestamp_ms,id,label,cx,cy
1710000000000,0,zone_de_decollage,640.0,360.0
```

**`aruco_debug.jpg` :** dernière image, avec les marqueurs retenus tracés dessus, mise à jour toutes les 2 secondes.

## Structure du projet

```
droneload/
├── flight/  navigation/  payload/  comms/  mission/   # Prévus
└── vision/                     # Détection des marqueurs
    ├── detect.py               # Boucle de détection et options en ligne de commande
    ├── camera_opencv.py        # Toute source lisible par cv2.VideoCapture
    ├── camera_rubikpi_csi.py   # Caméra CSI du RubikPi (pipeline GStreamer)
    └── camera_picamera2.py     # Caméra du Raspberry Pi
testing/
├── make_test_video.py          # Génère une vidéo de test avec des marqueurs en mouvement
└── benchmark.py                # Évalue la détection par rapport à la vérité terrain
tests/                          # Tests unitaires et de bout en bout
scripts/
├── check.sh                    # Lance tous les contrôles avec une sortie courte
├── setup.sh                    # Installe GStreamer et qtiqmmfsrc sur le RubikPi
├── test_camera.sh              # Teste le pipeline CSI sans OpenCV
└── build_opencv.sh             # Compile OpenCV avec GStreamer et aruco
docs/                           # Architecture et règles du concours
logs/                           # Journaux de branche et décisions
TODO.md                         # Problèmes connus et travail restant
```

`flight`, `navigation`, `payload`, `comms` et `mission` sont prévus et ne contiennent qu'un court README. Voir [`docs/architecture.md`](docs/architecture.md) (en anglais).

## Images de test

Les marqueurs de la vidéo générée par `testing/make_test_video.py` sont faciles à détecter : pour juger la qualité de la détection, utilisez des images réelles. Placez-les dans `test_footage/`, à la racine du dépôt. Git ignore ce dossier.

Aucun des deux jeux de données ci-dessous ne provient d'un drone ni n'utilise `DICT_4X4_50` : il faut donc préciser `--dict`.

**Téléchargement :**
```bash
mkdir -p test_footage/fdcl-gwu test_footage/shadow-aruco
curl -L -o test_footage/fdcl-gwu/test_video.mp4 \
    https://raw.githubusercontent.com/fdcl-gwu/aruco-markers/master/test_data/test_video.mp4
curl -L https://zenodo.org/api/records/10791293/files/video_5.tar.gz/content \
    | tar -xz -C test_footage/shadow-aruco
```

**Exécution :**
```bash
python3 -m droneload.vision --source test_footage/fdcl-gwu/test_video.mp4 --dict DICT_ARUCO_ORIGINAL
python3 -m droneload.vision --source "test_footage/shadow-aruco/video_5/%05d.png" --dict DICT_ARUCO_MIP_36h12
```

| Jeu de données | Contenu | Source | Licence |
|-----|---------|--------|---------|
| `fdcl-gwu` | 821 images en 1080p | [fdcl-gwu/aruco-markers](https://github.com/fdcl-gwu/aruco-markers) | BSD-3-Clause |
| `shadow-aruco` | 1 334 photos en 800×600 dans une pièce sombre avec des ombres mobiles, et vérité terrain dans `corrected_annotations/` | [Shadow-ArUco Dataset](https://doi.org/10.5281/zenodo.10791293), `video_5` | CC BY 4.0 |

## Contribuer

Les contributeurs et les agents de code suivent [`AGENTS.md`](AGENTS.md) (en anglais). Le travail se fait sur des branches, et chaque branche a son journal dans `logs/`.

**Agents :** lisez et utilisez les fichiers Markdown du projet, en n'ouvrant que ce qui est utile à la tâche :

- [`AGENTS.md`](AGENTS.md) : règles pour tout travail dans ce dépôt
- [`TODO.md`](TODO.md) : problèmes connus et travail restant
- [`docs/architecture.md`](docs/architecture.md) : modules et dépendances entre eux
- [`logs/DECISIONS.md`](logs/DECISIONS.md) : décisions durables
- [`docs/contest-rules.md`](docs/contest-rules.md) : règles provisoires de Droneload 2027, pour les questions sur le concours
- [`logs/`](logs/) : un journal par branche, où noter votre travail
- `README.fr.md` ou [`README.md`](README.md) : ce que fait le projet et comment le lancer

Avant de demander une revue, lancez :

```bash
pip install -r requirements-dev.txt
./scripts/check.sh
```

## Installation sur RubikPi 3

**Cette procédure n'a pas encore été validée sur la carte.**

Sur le RubikPi 3, la caméra CSI n'est accessible que par `qtiqmmfsrc`, un plugin GStreamer de Qualcomm. OpenCV doit donc prendre en charge GStreamer pour lire les images, ce qu'aucune version packagée ne permet avec aruco :

- `apt install python3-opencv` inclut GStreamer, mais la prise en charge d'aruco est incomplète.
- `pip install opencv-contrib-python` inclut aruco, mais pas GStreamer.

Il faut donc compiler OpenCV depuis les sources.

### 1. Cloner le dépôt

```bash
git clone https://github.com/fzizzle/droneload-ESILV-2026-2027.git
cd droneload-ESILV-2026-2027
```

### 2. Installer GStreamer et qtiqmmfsrc

```bash
./scripts/setup.sh
```

### 3. Tester la caméra

```bash
./scripts/test_camera.sh
```

Faites ce test avant la compilation, qui dure 1 à 2 heures. Appuyez sur Ctrl+C au bout de quelques secondes : le script doit afficher `Pipeline OK`.

En cas d'échec, essayez `video/x-raw(memory:GBM)` avec `qtivtransform` au lieu de `video/x-raw` seul avec `videoconvert`. Reportez la modification dans `droneload/vision/camera_rubikpi_csi.py` : les deux fichiers doivent utiliser le même pipeline.

### 4. Compiler OpenCV

```bash
./scripts/build_opencv.sh
```

Le script compile OpenCV 4.10.0 avec GStreamer et les modules contrib. Il doit se terminer par :

```
OpenCV version: 4.10.0
aruco OK: True
GStreamer: YES
```

### 5. Lancer le programme

```bash
python3 -m droneload.vision --source rubikpi-csi
```
