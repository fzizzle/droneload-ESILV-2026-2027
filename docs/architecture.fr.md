# Architecture

[English](architecture.md) | **Français**

Chaque module a une seule responsabilité. Les modules non commencés ne contiennent que de courts README.

| Module | Rôle | État |
|--------|------|------|
| `droneload/vision` | Lit les caméras et reconnaît les marqueurs ArUco, les affiches cibles et les lignes au sol | Détection ArUco uniquement |
| `droneload/flight` | Communique avec le contrôleur de vol via MAVLink et conserve ses réglages | Pas commencé |
| `droneload/navigation` | Se centre sur les cibles, explore le terrain et franchit la fenêtre | Pas commencé |
| `droneload/payload` | Saisit et relâche le disque | Pas commencé |
| `droneload/comms` | Communique avec le robot PULL-E et lit ses réponses | Pas commencé |
| `droneload/mission` | Exécute chaque épreuve étape par étape et montre au jury ce que le drone détecte | Pas commencé |

`testing/` contient les outils qui ne tournent jamais sur le drone : configuration du simulateur, benchmark et générateur de vidéo de test. `tests/` contient les tests automatisés, et `scripts/` les scripts d'installation et de contrôle.

## Dépendances

- `mission` appelle les autres modules. Eux n'appellent pas `mission`.
- `navigation` peut utiliser `vision` et `flight`.
- Tous les autres modules restent indépendants les uns des autres.
- Seul `flight` communique avec le contrôleur de vol, et seul `comms` communique avec le robot.
