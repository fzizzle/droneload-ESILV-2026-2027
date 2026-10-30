# Règles pour les agents

[English](AGENTS.md) | **Français**

Traduction pour les contributeurs. Les agents lisent la version anglaise, `AGENTS.md`, qui fait référence.

Règles pour chaque agent et contributeur. `AGENTS.md` est chargé à chaque session d'agent : gardez-le court.

## Contexte du projet

- Détection de marqueurs ArUco pour le concours Droneload 2027 (PI2 ESILV). La sortie se limite à des positions en pixels enregistrées.
- Le vol automatique rapporte la plupart des points de vol (670 sur 1 320 au total), et les règles 2027 sont provisoires. N'ouvrez `docs/contest-rules.md` que pour les questions sur le concours.
- Le matériel n'est pas choisi : gardez le code indépendant du matériel.
- Responsables : pas encore consignés. Demandez au chef de projet.

## Limiter la consommation

Certains contributeurs ont des forfaits gratuits.

- Ne lisez que ce dont la tâche a besoin : `TODO.md`, `logs/DECISIONS.md` et le journal de votre branche. N'ouvrez le README, les autres journaux ou d'autres fichiers que si nécessaire.
- N'ouvrez jamais `test_footage/`, des images ou des vidéos sauf si la tâche l'exige.
- Lancez `./scripts/check.sh` plutôt que des commandes séparées. Sa sortie est courte.
- Ne collez pas de longues sorties dans les journaux ou les pull requests. Résumez-les.
- N'utilisez le benchmark que pour les changements de détection.
- Travaillez sur un seul module à la fois.

## Méthode de travail

1. Créez une branche : `<type>/<description-courte>`, avec pour type `feature`, `fix`, `docs`, `test` ou `chore`. Ne committez jamais directement sur `main`.
2. Créez `logs/AAAA-MM-JJ-<nom-de-branche>.md` à partir de `logs/TEMPLATE.md`, en remplaçant `/` par `-`. Limitez-le à 20 lignes et mettez-le à jour au fil du travail.
3. Gardez un seul objectif par branche. Notez les problèmes sans rapport dans `TODO.md`.
4. Ajoutez les décisions durables à `logs/DECISIONS.md`, une ligne chacune.
5. Ouvrez une pull request indiquant ce qui a changé, comment cela a été vérifié et ce qui reste à faire.

Ne poussez que vers `origin`. Ne faites jamais de force-push sur des branches partagées et ne modifiez pas les entrées de journal d'un autre agent.

## S'arrêter et demander

Obtenez la décision d'une personne avant de :

- choisir ou supposer un matériel
- modifier les ID de marqueurs, les labels, le dictionnaire par défaut ou le format CSV
- ajouter une dépendance
- pousser vers `upstream` (`YUu-8/Droneload`, le dépôt de l'équipe précédente)
- écrire du code qui commande un drone ou communique avec un contrôleur de vol

## Code

- Suivez le style du code environnant. Ne refactorisez pas du code sans rapport.
- Utilisez la bibliothèque standard et les paquets standard avant d'écrire du code sur mesure.
- Respectez les limites des modules définies dans `docs/architecture.md`.
- Le code caméra va dans `droneload/vision/camera_*.py`, avec `open()`, `read()` et `release()`.
- Les réglages vont dans des constantes en haut du fichier principal de chaque module.
- `scripts/test_camera.sh` et `camera_rubikpi_csi.py` doivent utiliser le même pipeline.
- Ajoutez un test dans `tests/` pour chaque nouveau comportement ou correction de bug.
- Supprimez le code mort plutôt que de le commenter.

## Dépôt

- Ne committez jamais de fichiers générés ni d'images de test. Ajoutez les fichiers par leur nom.
- Utilisez UTF-8 et LF.
- Écrivez le code, les commentaires, les journaux et `TODO.md` en anglais.
- Écrivez les README, `docs/` et ce fichier en anglais et en français. Toute modification dans une langue doit être reportée dans l'autre (`*.fr.md`). Ne lisez que la version anglaise.

## Vérification

Depuis la racine du dépôt, une seule fois :

```bash
pip install -r requirements-dev.txt
```

Avant la relecture :

```bash
./scripts/check.sh
```

Pour les changements de détection, lancez aussi `python3 -m testing.benchmark` avant et après, et notez les deux résultats dans le journal. La référence est `found=56.4% unmatched=26.6%`. Les images sont listées dans le README. Réussir sur la vidéo de test générée ne prouve pas que la détection est bonne.

## Compte rendu

- Rapportez ce qui s'est passé, y compris les échecs et les contrôles non effectués.
- Le comportement de la caméra et de la carte ne compte comme testé que s'il a été exécuté sur ce matériel.
- Signalez comme non vérifiées les affirmations sur le matériel ou les paquets que vous n'avez pas contrôlées.

## Terminé signifie

- [ ] `./scripts/check.sh` réussit
- [ ] Le journal, `TODO.md` et les deux versions linguistiques sont à jour
- [ ] La pull request est ouverte
