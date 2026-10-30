# Résumé du concours Droneload 2027

[English](contest-rules.md) | **Français**

**Provisoire.** Ce résumé provient des diapositives de la première réunion des organisateurs et du portail des équipes (27 oct. 2026), car il n'existe pas encore de règlement écrit pour 2027. Là où les diapositives ne disent rien, le règlement 2026 sert de référence. Revérifiez chaque chiffre à la parution du PDF 2027.

## Échéances

| Date | Événement |
|------|-----------|
| 31 oct. 2026 | RCE1 (attendus non précisés) |
| 15 janv. 2027 | Clôture des inscriptions à la RCE2 |
| 23 janv. 2027 | RCE2 : une vidéo de vol stable rapporte +15 |
| 31 janv. 2027 | Clôture de l'adhésion à Planète Sciences |
| 24-25 avr. 2027 | RCE3 : un vol de 2 minutes en cage ou une vidéo de largage rapporte +45 |
| 30 mai 2027 | Clôture des droits à l'image |
| Non précisé | Versions intermédiaires du rapport, rapport final, oral, finale |

## Points

Total 1 320 : rapport 250, oral 250, épreuve de vol 670, bonus 150.

## Exigences pour le drone

- Classe 500 mm maximum, 3 kg maximum, 5 minutes d'autonomie, 200 m de portée radio.
- Reprise en main par le pilote à tout moment, failsafe en cas de perte radio ou de batterie faible, et fonction de coupure des moteurs.
- Kit de prêt : châssis DJI F450, Pixhawk 2, GPS, Flysky FS-i6, balises Marvelmind, flux optique PMW3901, télémétrie 433 MHz et ordinateur de bord sur demande.
- Règle 2026 : la mise sous tension nécessite l'accord du directeur des opérations de Planète Sciences sur place, sous peine de disqualification.

## Arène

Tapis d'environ 8 × 5 m dans une cage filet de 10 × 6 m. Des marqueurs imprimés sont posés sur le tapis. Les diapositives décrivent un vol en intérieur sans GNSS : prévoyez des balises, du flux optique ou de la vision. En 2026, l'épreuve de largage et de coopération s'est déroulée dans une cage extérieure : l'éclairage peut donc varier.

| Zone | Contenu |
|------|---------|
| A | Aire de décollage et d'atterrissage, avec ArUco |
| B | Environnement complexe : objets de plus de 50 cm de haut |
| C | Zone de largage et du robot, cibles 1 à 4 |
| D | Chemin sûr : une ligne, sans obstacle à moins de 50 cm de chaque côté |
| E | Une fenêtre de 100 × 100 cm : 4 ArUco aux coins à l'aller (facile), 2 au retour (difficile) |
| F | Totems en Akilux, du sol au toit de la cage |
| G | Barrière visuelle cachant des ArUco ; le robot la longe |

Le robot PULL-E porte un grand ArUco sur le dessus et envoie par UART un code indiquant la cible de largage. Il se pilote par UART ou par télécommande.

## Épreuve de vol

Une seule manche de 15 minutes, du démarrage des moteurs à l'arrêt des hélices. Les points indiqués sont les maximums en automatique. Une manche entièrement manuelle rapporte 40 points au plus.

| Partie | Tâches | Max |
|--------|--------|-----|
| 1 : Largage et coopération | Larguer sur les cibles annoncées, chercher et reconnaître les zones de livraison, se maintenir sur le robot, aligner le robot avec l'ArUco caché | 190 |
| 2 : Environnement complexe | Chemin sûr, fenêtre dans les deux sens, passage avec un objet, aller-retour automatique | 260 |
| Commun | Décollage et atterrissage automatiques ; deux missions entièrement automatiques à 100 chacune | 220 |

## Conseils logiciels des organisateurs

Utilisez OpenCV avec Python pour la vision, simulez le vol avec Gazebo et ArduPilot, et utilisez MAVLink avec QGroundControl ou Mission Planner. Testez chaque composant seul avant l'intégration.

## Marqueurs ArUco

Les ID 2027 ne sont pas publiés. `ARUCO_LABELS`, dans `droneload/vision/detect.py`, correspond à l'annexe 4 du règlement 2026, et les marqueurs 2026 mesuraient 20 × 20 cm et venaient d'un dictionnaire 4x4. 2026 comptait deux fenêtres et 12 marqueurs de fenêtre ; 2027 compte une fenêtre et 6 marqueurs : les ID 4 à 15 peuvent donc changer.

## Questions ouvertes

- Date et lieu de la finale, et attendus de la RCE1.
- Échéances du rapport et clôture des inscriptions à la RCE3.
- Les diapositives indiquent « 135 points max » par partie, mais les tableaux donnent 190 et 260.
- Le total manuel est annoncé à 40, mais les maximums par partie (20 et 30) font 50.
- Le protocole UART du robot est-il le même qu'en 2026 ?
