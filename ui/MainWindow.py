import time
from dataclasses import fields

import dearpygui.dearpygui as dpg

from config.Settings import GROUPS, validate
from core.Supervisor import FEATURE_REQUIREMENTS, FeatureState
from detection.Components import ComponentType
from ui.DetectionPreview import DetectionPreview
from Waypoints import list_routes


WARNING = (255, 200, 80)
ERROR = (255, 100, 100)
OK = (120, 220, 140)
MUTED = (170, 170, 170)

CLIENT_STATUS = {
    'none': 'No client selected',
    'found': 'Found',
    'minimized': 'Minimized',
    'not focused': 'Not focused',
    'lost': 'Lost',
}

# Settings groups shown on the Settings tab (route and client are chosen elsewhere)
SETTINGS_GROUPS = ('hotkeys', 'healing', 'mana', 'eating', 'attack_spells', 'cavebot')
SKIPPED_FIELDS = {('cavebot', 'route')}
LOG_REFRESH_S = 0.5


def state_text(status):
    if status.state is FeatureState.PAUSED:
        return f"Paused: {status.pause_reason}"
    return status.state.value.title()


class MainWindow:
    """ Control window. Calls Supervisor methods and reads its StatusSnapshot; never touches the game itself """

    def __init__(self, supervisor, store, settings, settings_warnings=()):
        self.supervisor = supervisor
        self.store = store
        self.settings = settings
        self.settings_warnings = list(settings_warnings)
        self._snapshot = None
        self._client_hwnds = {}
        self._routes = {}
        self._log_refreshed = 0.0
        self._log_cleared_at = 0.0
        self._last_selected = None
        self._shown_generation = None
        self.preview = None

    # ----- settings -----

    def _save_settings(self, settings):
        self.settings = settings
        self.store.save(settings)
        self.supervisor.apply_settings(settings)

    # ----- layout -----

    def build(self):
        dpg.create_context()
        dpg.create_viewport(title='MMORPG-Bot', width=440, height=600, always_on_top=True)
        self.preview = DetectionPreview()

        with dpg.window(tag='main') as main:
            self._build_header()
            with dpg.tab_bar(tag='tabs'):
                with dpg.tab(label='Run', tag='tab_run'):
                    self._build_run_tab()
                with dpg.tab(label='Detection', tag='tab_detection'):
                    self._build_detection_tab()
                with dpg.tab(label='Settings', tag='tab_settings'):
                    self._build_settings_tab()
                with dpg.tab(label='Log', tag='tab_log'):
                    self._build_log_tab()

        dpg.set_primary_window(main, True)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def _build_header(self):
        with dpg.group(horizontal=True):
            dpg.add_text('Client:')
            dpg.add_combo([], tag='client_combo', width=230, callback=self._on_client_selected,
                          no_preview=False, default_value='')
            dpg.add_text('', tag='client_status', color=MUTED)
        dpg.add_text('No Tibia client found', tag='no_client', color=WARNING)
        dpg.add_button(label='Start All', tag='start_all', width=-1, callback=self._on_start_stop_all)
        dpg.add_separator()

    def _build_run_tab(self):
        with dpg.table(header_row=True, borders_innerH=True, policy=dpg.mvTable_SizingStretchProp):
            dpg.add_table_column(label='On', width_fixed=True)
            dpg.add_table_column(label='Feature')
            dpg.add_table_column(label='State')
            dpg.add_table_column(label='', width_fixed=True)
            for status in self.supervisor.snapshot.features:
                key = status.key
                with dpg.table_row():
                    dpg.add_checkbox(tag=f"{key}_enabled", default_value=self.settings.features.enabled.get(key, False),
                                     callback=self._on_enabled, user_data=key)
                    dpg.add_text(status.label)
                    dpg.add_text('Off', tag=f"{key}_state")
                    dpg.add_button(label='Start', tag=f"{key}_button", width=50,
                                   callback=self._on_feature_button, user_data=key)
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_text('Route:')
            dpg.add_combo([], tag='route_combo', width=220, callback=self._on_route_selected)
        dpg.add_text('', tag='route_message', color=WARNING)
        self._refresh_routes()

    def _build_detection_tab(self):
        with dpg.group(horizontal=True):
            dpg.add_button(label='Detect now', callback=self._on_detect_now)
            dpg.add_text('No detection yet', tag='last_detection', color=MUTED)
        with dpg.table(header_row=True, borders_innerH=True):
            dpg.add_table_column(label='Component', width_fixed=True, init_width_or_weight=110)
            dpg.add_table_column(label='Status', width_fixed=True, init_width_or_weight=55)
            dpg.add_table_column(label='Details', width_stretch=True)
            for component_type in ComponentType:
                with dpg.table_row():
                    dpg.add_text(component_type.value)
                    dpg.add_text('-', tag=f"component_{component_type.name}_status")
                    dpg.add_text('', tag=f"component_{component_type.name}_info", wrap=215)
        with dpg.group(tag='preview_group'):
            self.preview.build('preview_group')

    def _build_settings_tab(self):
        with dpg.child_window(height=-60, border=False):
            for group in SETTINGS_GROUPS:
                values = getattr(self.settings, group)
                dpg.add_text(group.replace('_', ' ').title(), color=OK)
                for f in fields(GROUPS[group]):
                    if (group, f.name) in SKIPPED_FIELDS:
                        continue
                    tag = f"setting_{group}_{f.name}"
                    label = f.name.replace('_', ' ')
                    value = getattr(values, f.name)
                    if isinstance(value, bool):
                        dpg.add_checkbox(label=label, tag=tag, default_value=value)
                    elif isinstance(value, int):
                        dpg.add_input_int(label=label, tag=tag, default_value=value, width=120)
                    elif isinstance(value, float):
                        dpg.add_input_float(label=label, tag=tag, default_value=value, width=120, format='%.2f')
                    else:
                        dpg.add_input_text(label=label, tag=tag, default_value=str(value), width=120)
                dpg.add_spacer(height=4)
        dpg.add_text('\n'.join(self.settings_warnings), tag='settings_message', color=WARNING, wrap=400)
        with dpg.group(horizontal=True):
            dpg.add_button(label='Save', width=80, callback=self._on_save_settings)
            dpg.add_button(label='Revert', width=80, callback=self._on_revert_settings)

    def _build_log_tab(self):
        with dpg.group(horizontal=True):
            dpg.add_combo(['All', 'detection', 'supervisor'] + [s.key for s in self.supervisor.snapshot.features],
                          default_value='All', tag='log_filter', width=150)
            dpg.add_button(label='Clear', callback=self._on_clear_log)
        dpg.add_child_window(tag='log_lines', height=-1)

    # ----- callbacks (UI thread; never block) -----

    def _on_client_selected(self, sender, title):
        hwnd = self._client_hwnds.get(title)
        if hwnd is not None:
            self.supervisor.select_client(hwnd)
            self._save_settings(self.settings.with_group('client', last_title=title))

    def _on_start_stop_all(self):
        if self._snapshot is not None and self._snapshot.running:
            self.supervisor.stop_all()
        else:
            self.supervisor.start_all()

    def _on_enabled(self, sender, value, key):
        self._save_settings(self.settings.with_feature_enabled(key, value))
        if not value:
            self.supervisor.stop_feature(key)

    def _on_feature_button(self, sender, app_data, key):
        status = self._feature_status(key)
        if status is not None and status.state is not FeatureState.OFF:
            self.supervisor.stop_feature(key)
        else:
            self.supervisor.start_feature(key)

    def _on_route_selected(self, sender, label):
        route = self._routes.get(label)
        if route is None or not route.valid:
            if route is None:
                reason = 'unknown route'
            elif route.error:
                reason = route.error
            else:
                reason = 'missing marks: ' + ', '.join(route.missing)
            dpg.set_value('route_message', f"Route cannot be used ({reason})")
            dpg.set_value('route_combo', self._route_label(self.settings.cavebot.route))
            return
        dpg.set_value('route_message', '')
        self._save_settings(self.settings.with_group('cavebot', route=route.name))

    def _on_detect_now(self):
        self.supervisor.detect_now()

    def _on_save_settings(self):
        settings = self._settings_from_inputs()
        if settings is None:
            return
        problems = validate(settings)
        if problems:
            dpg.configure_item('settings_message', color=ERROR)
            dpg.set_value('settings_message', '\n'.join(problems))
            return
        self._save_settings(settings)
        dpg.configure_item('settings_message', color=OK)
        dpg.set_value('settings_message', 'Saved and applied')

    def _on_revert_settings(self):
        for group in SETTINGS_GROUPS:
            values = getattr(self.settings, group)
            for f in fields(GROUPS[group]):
                if (group, f.name) not in SKIPPED_FIELDS:
                    dpg.set_value(f"setting_{group}_{f.name}", getattr(values, f.name))
        dpg.configure_item('settings_message', color=MUTED)
        dpg.set_value('settings_message', 'Reverted')

    def _on_clear_log(self):
        self._log_cleared_at = time.time()
        dpg.delete_item('log_lines', children_only=True)

    # ----- helpers -----

    def _settings_from_inputs(self):
        settings = self.settings
        for group in SETTINGS_GROUPS:
            values = {}
            for f in fields(GROUPS[group]):
                if (group, f.name) in SKIPPED_FIELDS:
                    continue
                value = dpg.get_value(f"setting_{group}_{f.name}")
                if group == 'hotkeys':
                    value = value.strip().lower()
                values[f.name] = value
            settings = settings.with_group(group, **values)
        return settings

    def _feature_status(self, key):
        if self._snapshot is None:
            return None
        return next((s for s in self._snapshot.features if s.key == key), None)

    def _route_label(self, name):
        for label, route in self._routes.items():
            if route.name == name:
                return label
        return ''

    def _refresh_routes(self):
        self._routes = {}
        for route in list_routes():
            label = route.name if route.valid else f"{route.name} (invalid)"
            self._routes[label] = route
        dpg.configure_item('route_combo', items=list(self._routes))
        dpg.set_value('route_combo', self._route_label(self.settings.cavebot.route))

    # ----- per-frame refresh -----

    def refresh(self):
        snapshot = self.supervisor.snapshot
        if snapshot is not self._snapshot:
            self._snapshot = snapshot
            self._refresh_header(snapshot)
            self._refresh_features(snapshot)
            self._refresh_detection(snapshot)
        if time.monotonic() - self._log_refreshed >= LOG_REFRESH_S:
            self._log_refreshed = time.monotonic()
            self._refresh_log()

    def _refresh_header(self, snapshot):
        titles = [c.title for c in snapshot.clients]
        self._client_hwnds = {c.title: c.hwnd for c in snapshot.clients}
        dpg.configure_item('client_combo', items=titles)
        selected = next((c.title for c in snapshot.clients if c.hwnd == snapshot.selected_hwnd), '')
        dpg.set_value('client_combo', selected)
        dpg.configure_item('no_client', show=not titles)
        dpg.set_value('client_status', CLIENT_STATUS.get(snapshot.client_state, snapshot.client_state))
        dpg.configure_item('start_all', label='Stop All' if snapshot.running else 'Start All',
                           enabled=snapshot.running or snapshot.selected_hwnd is not None)
        if snapshot.selected_hwnd != self._last_selected and selected:
            self._last_selected = snapshot.selected_hwnd
            if self.settings.client.last_title != selected:
                self._save_settings(self.settings.with_group('client', last_title=selected))

    def _refresh_features(self, snapshot):
        has_client = snapshot.selected_hwnd is not None
        for status in snapshot.features:
            dpg.set_value(f"{status.key}_state", state_text(status))
            running = status.state is not FeatureState.OFF
            dpg.configure_item(f"{status.key}_button", label='Stop' if running else 'Start',
                               enabled=running or has_client)

    def _refresh_detection(self, snapshot):
        layout = snapshot.layout
        if layout is None or layout.generation == self._shown_generation:
            return
        self._shown_generation = layout.generation
        if snapshot.detection_seconds is not None:
            dpg.set_value('last_detection', f"Last detection {time.strftime('%H:%M:%S')} "
                                            f"took {snapshot.detection_seconds:.2f} s")
        for component_type, component in layout.components.items():
            name = component_type.name
            if component.found:
                dpg.set_value(f"component_{name}_status", 'Found')
                dpg.configure_item(f"component_{name}_status", color=OK)
                region = component.region
                dpg.set_value(f"component_{name}_info", f"{component.score:.2f} / {region.width}x{region.height}")
            else:
                affected = [k for k, needs in FEATURE_REQUIREMENTS.items() if component_type in needs]
                dpg.set_value(f"component_{name}_status", 'Missing')
                dpg.configure_item(f"component_{name}_status", color=WARNING)
                details = component.missing_reason or ''
                if affected:
                    details += '; needed by ' + ', '.join(affected)
                dpg.set_value(f"component_{name}_info", details)
        self.preview.update(layout, snapshot.capture)

    def _refresh_log(self):
        source = dpg.get_value('log_filter')
        entries = self.supervisor.log.entries(100, None if source == 'All' else source)
        entries = [e for e in entries if e.time > self._log_cleared_at]
        dpg.delete_item('log_lines', children_only=True)
        colours = {'warning': WARNING, 'error': ERROR}
        for entry in entries:
            stamp = time.strftime('%H:%M:%S', time.localtime(entry.time))
            dpg.add_text(f"{stamp} [{entry.source}] {entry.message}", parent='log_lines',
                         color=colours.get(entry.level, (230, 230, 230)), wrap=400)

    # ----- loop -----

    def run(self):
        """ Renders until the window is closed """
        while dpg.is_dearpygui_running():
            self.refresh()
            dpg.render_dearpygui_frame()
        dpg.destroy_context()
