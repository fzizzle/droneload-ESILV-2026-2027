# Droneload : détection de marqueurs ArUco en temps réel

[English](README.md) | **Français**

Droneload est le logiciel de notre équipe pour le concours Droneload 2027, une compétition étudiante organisée par Planète Sciences. Les équipes construisent un multirotor qui effectue seul des missions en intérieur : il lit des marqueurs ArUco, largue de petits objets sur des cibles et coopère avec un robot au sol.

Pour l'instant, ce dépôt contient la détection ArUco. Le programme lit une caméra ou une vidéo, attribue un label à chaque marqueur et enregistre son centre en pixels. La boucle de détection n'utilise pas encore la distance des marqueurs, et n'envoie rien au contrôleur de vol. Il a été écrit pour le RubikPi 3 (Qualcomm QCS6490), mais il fonctionne sur toute machine équipée d'OpenCV.

## Structure du projet

```
droneload/
├── flight/  navigation/  payload/  comms/  mission/   # Prévus
└── vision/                     # Détection des marqueurs
    ├── detect.py               # Boucle de détection et options en ligne de commande
    ├── pose.py                 # Position du marqueur en mètres
    ├── camera_opencv.py        # Toute source lisible par cv2.VideoCapture
    ├── camera_rubikpi_csi.py   # Caméra CSI du RubikPi (pipeline GStreamer)
    ├── camera_picamera2.py     # Caméra du Raspberry Pi
    └── tracking/               # Prévu : stabilise les détections d'une image à l'autre
testing/
├── make_test_video.py          # Génère une vidéo de test avec des marqueurs en mouvement
├── benchmark.py                # Évalue la détection par rapport à la vérité terrain
└── vibration_test.py           # Simule le flou et les ondulations, et mesure la détection
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

## Installation

Suivez la section qui correspond à votre ordinateur. Cette installation ne se fait qu'une fois. Pour lancer le projet sur un RubikPi, voir [Installation sur RubikPi 3](#installation-sur-rubikpi-3).

### Mac

**1. Installez les outils.** Passez ceux que vous avez déjà.

- Python 3 : téléchargez-le sur [python.org/downloads](https://www.python.org/downloads/) et lancez l'installateur.
- Visual Studio Code : téléchargez-le sur [code.visualstudio.com](https://code.visualstudio.com/) et glissez-le dans Applications.

**2. Ouvrez le Terminal.** Appuyez sur Cmd+Espace, tapez `Terminal`, puis appuyez sur Entrée.

**3. Installez Git et téléchargez le projet.** Lancez ces commandes une par une. Si la première indique que les outils sont déjà installés, continuez. Sinon, cliquez sur **Installer** dans la fenêtre qui s'affiche et attendez la fin de l'installation.

```bash
xcode-select --install
cd ~/Documents
git clone https://github.com/fzizzle/droneload-ESILV-2026-2027.git
```

**4. Allez dans le dossier du projet.**

```bash
cd droneload-ESILV-2026-2027
```

**5. Ouvrez le projet dans VS Code.** Ouvrez VS Code, appuyez sur Cmd+Maj+P, tapez `Shell Command: Install 'code' command in PATH`, puis appuyez sur Entrée. Revenez ensuite dans le Terminal et lancez :

```bash
code .
```

**6. Configurez Python.** Dans VS Code, choisissez **Terminal > New Terminal**, puis lancez :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

La ligne du terminal commence maintenant par `(.venv)`. Relancez la ligne `source` chaque fois que vous ouvrez un nouveau terminal.

**7. Faites un essai.** Aucune caméra n'est nécessaire :

```bash
python -m testing.make_test_video
python -m droneload.vision --source test_markers.mp4
```

La dernière ligne doit indiquer `Detections saved to detections.csv`. Les résultats se trouvent dans `detections.csv` et `aruco_debug.jpg`.

### Windows

**1. Installez les outils.** Passez ceux que vous avez déjà.

- Git : téléchargez-le sur [git-scm.com](https://git-scm.com/downloads) et gardez les options par défaut.
- Python 3 : téléchargez-le sur [python.org/downloads](https://www.python.org/downloads/). Sur le premier écran de l'installateur, cochez **Add python.exe to PATH**.
- Visual Studio Code : téléchargez-le sur [code.visualstudio.com](https://code.visualstudio.com/) et gardez les options par défaut.

**2. Ouvrez PowerShell.** Appuyez sur la touche Windows, tapez `PowerShell`, puis appuyez sur Entrée. S'il était déjà ouvert, fermez-le et rouvrez-le pour qu'il trouve les nouveaux outils.

**3. Téléchargez le projet.** Lancez ces commandes une par une :

```powershell
cd $HOME\Documents
git clone https://github.com/fzizzle/droneload-ESILV-2026-2027.git
```

**4. Allez dans le dossier du projet.**

```powershell
cd droneload-ESILV-2026-2027
```

**5. Ouvrez le projet dans VS Code.**

```powershell
code .
```

**6. Configurez Python.** Dans VS Code, choisissez **Terminal > New Terminal**, puis lancez :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Si la deuxième ligne indique que l'exécution de scripts est désactivée, lancez une fois la commande suivante, puis relancez cette ligne :

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

La ligne du terminal commence maintenant par `(.venv)`. Relancez la ligne `Activate.ps1` chaque fois que vous ouvrez un nouveau terminal.

**7. Faites un essai.** Aucune caméra n'est nécessaire :

```powershell
python -m testing.make_test_video
python -m droneload.vision --source test_markers.mp4
```

La dernière ligne doit indiquer `Detections saved to detections.csv`. Les résultats se trouvent dans `detections.csv` et `aruco_debug.jpg`.

## État du projet

| Élément | État |
|---------|------|
| Détection, labels et enregistrement | Testés sur PC, sur des images générées et réelles |
| Caméra CSI du RubikPi | Non testée sur la carte ; le pipeline devra peut-être être adapté |
| Matériel | Kit de prêt des organisateurs retenu par hypothèse, avec un ordinateur de bord Qualcomm (modèle à confirmer) ; caméras à acheter |
| Marqueurs du projet (`DICT_4X4_50`) | Non testés sur des images réelles |

Sur les images de test Shadow-ArUco, le détecteur a trouvé 56 % des marqueurs annotés, et 27 % de ses détections ne correspondaient à aucune annotation. Ces images utilisent un autre dictionnaire, si bien que ces chiffres ne valent pas forcément pour les marqueurs du projet. Le travail restant figure dans `TODO.md`.

## Utilisation

```bash
python -m droneload.vision [--source SOURCE] [--dict DICTIONNAIRE]
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

Les labels sont définis dans `ARUCO_LABELS`, dans `detect.py`. Les autres ID apparaissent sous la forme `unknown_N`. Ils suivent le règlement V0 de 2027.

| ID | Label |
|----|-------|
| 0 | `zone_de_decollage` |
| 1 | `robot` |
| 2-3 | `align` |
| 4-7 | `fenetre_recto_*` (droite/gauche, haut/bas) |
| 8-9 | `fenetre_verso_*` (haut/bas) |

### Sorties

**Terminal, toutes les 2 secondes :**
```
[14:32:01] detect=3.2ms
  ID= 0  label=zone_de_decollage                         center=(640.0,360.0)
  ID= 4  label=fenetre_recto_droite_bas                  center=(213.5,180.2)
```

**`detections.csv` :**
```
timestamp_ms,id,label,cx,cy
1710000000000,0,zone_de_decollage,640.0,360.0
```

**`aruco_debug.jpg` :** dernière image, avec les marqueurs retenus tracés dessus, mise à jour toutes les 2 secondes.

## Images de test

Les marqueurs de la vidéo générée par `testing/make_test_video.py` sont faciles à détecter : pour juger la qualité de la détection, utilisez des images réelles. Placez-les dans `test_footage/`, à la racine du dépôt. Git ignore ce dossier.

Aucun des deux jeux de données ci-dessous ne provient d'un drone ni n'utilise `DICT_4X4_50` : il faut donc préciser `--dict`.

**Téléchargement.** Sous Windows, lancez ceci dans **Git Bash** :
```bash
mkdir -p test_footage/fdcl-gwu test_footage/shadow-aruco
curl -L -o test_footage/fdcl-gwu/test_video.mp4 \
    https://raw.githubusercontent.com/fdcl-gwu/aruco-markers/master/test_data/test_video.mp4
curl -L https://zenodo.org/api/records/10791293/files/video_5.tar.gz/content \
    | tar -xz -C test_footage/shadow-aruco
```

**Exécution :**
```bash
python -m droneload.vision --source test_footage/fdcl-gwu/test_video.mp4 --dict DICT_ARUCO_ORIGINAL
python -m droneload.vision --source "test_footage/shadow-aruco/video_5/%05d.png" --dict DICT_ARUCO_MIP_36h12
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
./scripts/check.sh
```

Sous Windows, lancez-le dans **Git Bash** plutôt que dans PowerShell, depuis le dossier du projet :

```bash
source .venv/Scripts/activate
bash scripts/check.sh
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
