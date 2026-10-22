from core.Dpi import make_dpi_aware

# Before anything that reads coordinates is imported
make_dpi_aware()

from config.Settings import SettingsStore  # noqa: E402
from core.Supervisor import Supervisor  # noqa: E402
from modules.AttackSpells import AttackSpellsFeature  # noqa: E402
from modules.CaveBot import AttackFeature, LootFeature, WalkFeature  # noqa: E402
from modules.Healing import HealingFeature, ManaRefillFeature  # noqa: E402
from modules.Utils import ChaseFeature, EatingFeature  # noqa: E402
from ui.MainWindow import MainWindow  # noqa: E402


def create_features():
    """ Every feature, in the order shown in the UI """
    return [
        HealingFeature(),
        ManaRefillFeature(),
        EatingFeature(),
        AttackSpellsFeature(),
        ChaseFeature(),
        AttackFeature(),
        LootFeature(),
        WalkFeature(),
    ]


def main():
    store = SettingsStore()
    settings, warnings = store.load()
    supervisor = Supervisor(settings)
    for warning in warnings:
        supervisor.log.add('settings', warning, 'warning')
    for feature in create_features():
        supervisor.register(feature)
    supervisor.start()

    window = MainWindow(supervisor, store, settings, warnings)
    window.build()
    try:
        window.run()
    finally:
        supervisor.shutdown(timeout=2.0)


if __name__ == "__main__":
    main()
