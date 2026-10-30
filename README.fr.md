# Droneload : détection de marqueurs ArUco en temps réel

[English](README.md) | **Français**

Ce programme détecte des marqueurs ArUco à partir d'une caméra ou d'une vidéo enregistrée, leur attribue un label et enregistre leur position dans l'image. Il a été écrit pour le RubikPi 3 (Qualcomm QCS6490), mais fonctionne sur toute machine disposant d'OpenCV.

La sortie est le centre de chaque marqueur, en pixels. Le programme n'estime ni la pose ni la distance, et n'envoie rien à un contrôleur de vol.

## État du projet

| Élément | État |
|---------|------|
| Détection, labels et journalisation | Testés sur PC avec des images générées et réelles |
| Caméra CSI du RubikPi | Non testée sur une carte ; le pipeline devra peut-être être modifié |
| Matériel | Pas encore choisi |
| Marqueurs du projet (`DICT_4X4_50`) | Non testés sur des images réelles |

Sur les images de test Shadow-ArUco, le détecteur a trouvé 56 % des marqueurs annotés, et 27 % de ses détections ne correspondaient pas aux annotations. Ces images utilisent un autre dictionnaire : ces chiffres ne s'appliquent donc pas forcément aux marqueurs du projet. Le travail restant est suivi dans `TODO.md`.

## Démarrage rapide

Il faut Python 3 et un PC. Toutes les commandes se lancent depuis la racine du dépôt.

```bash
pip install opencv-contrib-python
python3 -m testing.make_test_video          # aucune caméra nécessaire
python3 -m droneload.vision --source test_markers.mp4
```

Les résultats sont écrits dans `detections.csv` et `aruco_debug.jpg`.

## Utilisation

```bash
python3 -m droneload.vision [--source SOURCE] [--dict DICTIONNAIRE]
```

Par défaut, `--source` vaut `0`, la première webcam. Valeurs acceptées :

| Valeur | Source |
|--------|--------|
| `0`, `1`, ... | Webcam ou autre caméra |
| `video.mp4` | Fichier vidéo |
| `"frames/%03d.jpg"` | Séquence d'images |
| Pipeline GStreamer | Nécessite OpenCV compilé avec GStreamer |
| `rubikpi-csi` | Caméra CSI du RubikPi |
| `picamera` | Caméra du Raspberry Pi, nécessite `picamera2` |

`--dict` prend le nom d'un dictionnaire `cv2.aruco` et vaut `DICT_4X4_50` par défaut.

Les sources vidéo et image s'arrêtent à la dernière image. Pour arrêter une source en direct, appuyez sur Ctrl+C.

## Fonctionnement

1. Lit une image depuis la source.
2. La convertit en niveaux de gris et applique un rehaussement de contraste CLAHE, qui améliore la détection en faible lumière.
3. Détecte les marqueurs et écarte ceux dont un côté mesure moins de 10 pixels (`MIN_SIDE_PX` dans `detect.py`).
4. Associe chaque ID à un label.
5. Enregistre chaque ID au plus une fois par seconde (`WRITE_COOLDOWN_MS`), ce qui limite la taille du CSV. Cette limite suit le temps réel : une vidéo traitée plus vite que sa durée produit donc moins de lignes.

Les marqueurs doivent avoir une bordure blanche pour être détectés.

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

**`aruco_debug.jpg` :** dernière image avec les marqueurs acceptés dessinés, mise à jour toutes les 2 secondes.

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

`flight`, `navigation`, `payload`, `comms` et `mission` sont prévus et ne contiennent qu'un court README. Voir [`docs/architecture.fr.md`](docs/architecture.fr.md).

## Images de test

La vidéo de `testing/make_test_video.py` est facile à détecter : utilisez des images réelles pour juger la qualité de détection. Elles se placent dans `test_footage/`, à la racine du dépôt, un dossier ignoré par git.

Aucun des deux jeux ci-dessous ne provient d'un drone ni n'utilise `DICT_4X4_50` : les deux nécessitent donc `--dict`.

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

| Jeu | Contenu | Source | Licence |
|-----|---------|--------|---------|
| `fdcl-gwu` | 821 images en 1080p | [fdcl-gwu/aruco-markers](https://github.com/fdcl-gwu/aruco-markers) | BSD-3-Clause |
| `shadow-aruco` | 1 334 photos en 800×600 dans une pièce sombre avec des ombres mobiles, vérité terrain dans `corrected_annotations/` | [Shadow-ArUco Dataset](https://doi.org/10.5281/zenodo.10791293), `video_5` | CC BY 4.0 |

## Contribuer

Les contributeurs et les agents de code suivent [`AGENTS.fr.md`](AGENTS.fr.md). Le travail se fait sur des branches, et chaque branche a un journal dans `logs/`.

**Agents :** lisez et utilisez les fichiers Markdown du projet, en n'ouvrant que ce dont la tâche a besoin :

- [`AGENTS.fr.md`](AGENTS.fr.md) : règles pour tout travail dans ce dépôt
- [`TODO.md`](TODO.md) : problèmes connus et travail restant
- [`docs/architecture.fr.md`](docs/architecture.fr.md) : modules et dépendances entre eux
- [`logs/DECISIONS.md`](logs/DECISIONS.md) : décisions durables
- [`docs/contest-rules.fr.md`](docs/contest-rules.fr.md) : règles provisoires de Droneload 2027, pour les questions sur le concours
- [`logs/`](logs/) : un journal par branche, où noter votre travail
- [`README.md`](README.md) ou `README.fr.md` : ce que fait le projet et comment le lancer

Avant de demander une relecture, lancez :

```bash
pip install -r requirements-dev.txt
./scripts/check.sh
```

## Installation sur RubikPi 3

**Cette procédure n'a pas été confirmée sur une carte.**

Sur le RubikPi 3, la caméra CSI n'est accessible que par `qtiqmmfsrc`, un plugin GStreamer de Qualcomm. OpenCV doit donc prendre en charge GStreamer pour lire les images. Il manque quelque chose à chaque version packagée :

- `apt install python3-opencv` inclut GStreamer, mais le support d'aruco est incomplet.
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

Lancez ce test avant la compilation, qui prend 1 à 2 heures. Appuyez sur Ctrl+C après quelques secondes. Le script doit afficher `Pipeline OK`.

En cas d'échec, essayez `video/x-raw(memory:GBM)` avec `qtivtransform` à la place de `video/x-raw` simple avec `videoconvert`. Faites la même modification dans `droneload/vision/camera_rubikpi_csi.py`, car les deux fichiers doivent utiliser le même pipeline.

### 4. Compiler OpenCV

```bash
./scripts/build_opencv.sh
```

Le script compile OpenCV 4.10.0 avec GStreamer et les modules contrib. Vérifiez qu'il se termine par :

```
OpenCV version: 4.10.0
aruco OK: True
GStreamer: YES
```

### 5. Lancer le programme

```bash
python3 -m droneload.vision --source rubikpi-csi
```
