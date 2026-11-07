"""Internationalization (i18n) localization module for Command Center."""

from __future__ import annotations

from typing import Dict

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ["en", "fr"]

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # App Header & Meta
        "app_subtitle": "• Modern Windows Terminal",
        "header_settings": "F10 Settings",
        # Quick Action Buttons
        "qa_files": "📁 Files",
        "qa_repos": "🌿 Repos",
        "qa_procs": "⚡ Top Apps",
        "qa_disks": "💾 Disks",
        "qa_ping": "🌐 Ping",
        "qa_library": "📚 Library",
        "qa_shell": "🔄 Shell",
        "qa_clear": "🧹 Clear",
        # Repo Navigator Screen
        "repo_dialog_title": "GIT REPOSITORIES & NAVIGATION",
        "repo_search_placeholder": "Search repositories by name, branch, or path... (Esc to close)",
        "repo_dialog_hint": "[Enter] Navigate to Repo  •  [Esc] Close",
        "repo_btn_navigate": "➔ Navigate to Repo (Enter)",
        "repo_btn_cancel": "Cancel (Esc)",
        "repo_active_badge": "★ Current",
        "repo_switched": "Switched to repository:",
        # Input Placeholders
        "placeholder_ps": "Type a PowerShell command or click a quick action above...",
        "placeholder_cmd": "Type a CMD command or click a quick action above...",
        # Status Bar Badges
        "status_ready": "Ready",
        "status_running": "Running...",
        "status_exit": "Exit",
        "repo_label": "Repo",
        "root_label": "Root",
        "branch_label": "Branch",
        # Keybindings Footer
        "key_quit": "Quit",
        "key_switch_shell": "Switch Shell (F2)",
        "key_theme": "Theme",
        "key_palette": "Palette/Help",
        "key_library": "Library",
        "key_history": "History",
        "key_settings": "Settings (F10)",
        "key_interrupt": "Interrupt/Clear",
        "key_restart": "Restart Shell",
        "key_copy_output": "Copy Output",
        # Settings Screen
        "settings_title": "SETTINGS & PREFERENCES",
        "settings_lang_label": "Interface Language:",
        "settings_lang_btn": "Language",
        "settings_theme_label": "Interface Theme:",
        "settings_theme_btn": "Theme",
        "settings_shell_label": "Default Shell:",
        "settings_shell_btn": "Shell",
        "settings_lib_label": "Library Enter Behavior:",
        "settings_lib_btn": "Enter Action",
        "settings_retention_label": "History Output Retention:",
        "settings_retention_btn": "Retention",
        "settings_safety_label": "Dangerous Command Safety Check:",
        "settings_safety_btn": "Safety",
        "safety_enabled_str": "ENABLED (Confirm before run)",
        "safety_disabled_str": "DISABLED",
        "settings_save_btn": "Save Preferences (Enter)",
        "settings_cancel_btn": "Cancel (Esc)",
        "settings_saved_notify": "Settings saved successfully!",
        # Safety Dialog
        "safety_dialog_title": "⚠️ SAFETY CONFIRMATION: DANGEROUS COMMAND DETECTED",
        "safety_dialog_desc": "The following command matches a known destructive pattern and may modify or delete system files:",
        "safety_dialog_cancel": "Cancel & Go Back (Esc)",
        "safety_dialog_run": "Run Anyway (Ctrl+Enter)",
        # Library Screen
        "lib_title": "COMMAND LIBRARY",
        "lib_search_placeholder": "Search library by name, command, description, or tags... (Esc to close)",
        "lib_tier_all": "All Commands (1)",
        "lib_tier_everyday": "★ Everyday Commands (2)",
        "lib_tier_specialized": "⚙ Specialized Commands (3)",
        "lib_shell_all": "All Shells",
        "lib_favs_only": "Favorites Only",
        "lib_add_btn": "+ Add (a)",
        "lib_sync_tldr": "Sync tldr (s)",
        "lib_export": "Export (x)",
        "lib_import": "Import (i)",
        # Palette Screen
        "palette_title": "COMMAND PALETTE & QUICK HELP",
        "palette_search_placeholder": "Search commands, shortcuts, or tools (e.g. ip, disk, clean)... (Esc to close)",
        "palette_tab_all": "All Shells",
        "palette_tab_everyday": "★ Everyday",
        "palette_tab_specialized": "⚙ Specialized",
        "palette_tab_shortcuts": "⌨ Shortcuts",
        # History Screen
        "history_title": "COMMAND HISTORY",
        "history_search_placeholder": "Filter history by command or output... (Esc to close)",
        "history_clear_btn": "Clear History",
    },
    "fr": {
        # App Header & Meta
        "app_subtitle": "• Terminal Moderne Windows",
        "header_settings": "F10 Paramètres",
        # Quick Action Buttons
        "qa_files": "📁 Fichiers",
        "qa_repos": "🌿 Dépôts",
        "qa_procs": "⚡ Applications",
        "qa_disks": "💾 Disques",
        "qa_ping": "🌐 Ping",
        "qa_library": "📚 Bibliothèque",
        "qa_shell": "🔄 Shell",
        "qa_clear": "🧹 Effacer",
        # Repo Navigator Screen
        "repo_dialog_title": "DÉPÔTS GIT & NAVIGATION",
        "repo_search_placeholder": "Rechercher dépôts par nom, branche ou chemin... (Échap pour fermer)",
        "repo_dialog_hint": "[Entrée] Naviguer vers le dépôt  •  [Échap] Fermer",
        "repo_btn_navigate": "➔ Naviguer vers le dépôt (Entrée)",
        "repo_btn_cancel": "Annuler (Échap)",
        "repo_active_badge": "★ Actuel",
        "repo_switched": "Navigation vers le dépôt :",
        # Input Placeholders
        "placeholder_ps": "Tapez une commande PowerShell ou cliquez sur une action rapide...",
        "placeholder_cmd": "Tapez une commande CMD ou cliquez sur une action rapide...",
        # Status Bar Badges
        "status_ready": "Prêt",
        "status_running": "Exécution...",
        "status_exit": "Sortie",
        "repo_label": "Dépôt",
        "root_label": "Racine",
        "branch_label": "Branche",
        # Keybindings Footer
        "key_quit": "Quitter",
        "key_switch_shell": "Changer Shell (F2)",
        "key_theme": "Thème",
        "key_palette": "Palette/Aide",
        "key_library": "Bibliothèque",
        "key_history": "Historique",
        "key_settings": "Paramètres (F10)",
        "key_interrupt": "Interrompre/Effacer",
        "key_restart": "Redémarrer Shell",
        "key_copy_output": "Copier Sortie",
        # Settings Screen
        "settings_title": "PARAMÈTRES & PRÉFÉRENCES",
        "settings_lang_label": "Langue de l'interface :",
        "settings_lang_btn": "Langue",
        "settings_theme_label": "Thème de l'interface :",
        "settings_theme_btn": "Thème",
        "settings_shell_label": "Shell par défaut :",
        "settings_shell_btn": "Shell",
        "settings_lib_label": "Comportement Entrée (Bibliothèque) :",
        "settings_lib_btn": "Action Entrée",
        "settings_retention_label": "Rétention de l'historique :",
        "settings_retention_btn": "Rétention",
        "settings_safety_label": "Contrôle de sécurité des commandes :",
        "settings_safety_btn": "Sécurité",
        "safety_enabled_str": "ACTIVÉ (Confirmer avant exécution)",
        "safety_disabled_str": "DÉSACTIVÉ",
        "settings_save_btn": "Enregistrer les préférences (Entrée)",
        "settings_cancel_btn": "Annuler (Échap)",
        "settings_saved_notify": "Paramètres enregistrés avec succès !",
        # Safety Dialog
        "safety_dialog_title": "⚠️ CONFIRMATION DE SÉCURITÉ : COMMANDE DANGEREUSE",
        "safety_dialog_desc": "La commande suivante correspond à un motif destructeur connu et peut modifier ou supprimer des fichiers système :",
        "safety_dialog_cancel": "Annuler & Revenir (Échap)",
        "safety_dialog_run": "Exécuter quand même (Ctrl+Entrée)",
        # Library Screen
        "lib_title": "BIBLIOTHÈQUE DE COMMANDES",
        "lib_search_placeholder": "Rechercher par nom, commande, description ou tag... (Échap pour fermer)",
        "lib_tier_all": "Toutes les commandes (1)",
        "lib_tier_everyday": "★ Commandes courantes (2)",
        "lib_tier_specialized": "⚙ Commandes spécialisées (3)",
        "lib_shell_all": "Tous les shells",
        "lib_favs_only": "Favoris uniquement",
        "lib_add_btn": "+ Ajouter (a)",
        "lib_sync_tldr": "Sync tldr (s)",
        "lib_export": "Exporter (x)",
        "lib_import": "Importer (i)",
        # Palette Screen
        "palette_title": "PALETTE DE COMMANDES & AIDE RAPIDE",
        "palette_search_placeholder": "Rechercher commandes, raccourcis ou outils... (Échap pour fermer)",
        "palette_tab_all": "Tous les shells",
        "palette_tab_everyday": "★ Courantes",
        "palette_tab_specialized": "⚙ Spécialisées",
        "palette_tab_shortcuts": "⌨ Raccourcis",
        # History Screen
        "history_title": "HISTORIQUE DES COMMANDES",
        "history_search_placeholder": "Filtrer l'historique par commande ou sortie... (Échap pour fermer)",
        "history_clear_btn": "Effacer l'historique",
    },
}


def t(key: str, lang: str = "en") -> str:
    """Translate key to specified language with fallback to English."""
    lang_dict = TRANSLATIONS.get(lang.lower(), TRANSLATIONS[DEFAULT_LANGUAGE])
    if key in lang_dict:
        return lang_dict[key]
    return TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
