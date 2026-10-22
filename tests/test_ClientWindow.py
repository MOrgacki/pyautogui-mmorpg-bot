from unittest import TestCase

from core.ClientWindow import WindowState, find_client_windows
from detection.Components import Region
from tests.fakes import OFFICIAL_EXE, FakeWindow, FakeWindowApi


class TestFindClientWindows(TestCase):

    def test_filters_to_official_client(self):
        api = FakeWindowApi([
            FakeWindow(1, 'Tibia - Knight', OFFICIAL_EXE),
            FakeWindow(2, 'Tibia - Wiki - Google Chrome', r'C:\Program Files\Google\Chrome\chrome.exe'),
            FakeWindow(3, 'Tibia', r'C:\Games\OTClient\otclient.exe'),
            FakeWindow(4, 'Tibia - Hidden', OFFICIAL_EXE, visible=False),
            FakeWindow(5, 'Notepad', r'C:\Windows\notepad.exe'),
        ], foreground=1)
        clients = find_client_windows(api=api)
        self.assertEqual([c.hwnd for c in clients], [1])
        self.assertEqual(clients[0].client_rect, Region(100, 50, 800, 600))
        self.assertTrue(clients[0].is_foreground)
        self.assertIs(clients[0].state, WindowState.VISIBLE)

    def test_minimized_client(self):
        api = FakeWindowApi([FakeWindow(1, 'Tibia - Knight', OFFICIAL_EXE, minimized=True)])
        clients = find_client_windows(api=api)
        self.assertIs(clients[0].state, WindowState.MINIMIZED)
        self.assertIsNone(clients[0].client_rect)

    def test_lost_after_close(self):
        window = FakeWindow(1, 'Tibia - Knight', OFFICIAL_EXE)
        api = FakeWindowApi([window], foreground=1)
        client = find_client_windows(api=api)[0]
        window.exists = False
        self.assertIs(client.refresh().state, WindowState.LOST)
        self.assertFalse(client.is_foreground)

    def test_refresh_tracks_resize_and_focus(self):
        window = FakeWindow(1, 'Tibia - Knight', OFFICIAL_EXE)
        api = FakeWindowApi([window], foreground=1)
        client = find_client_windows(api=api)[0]
        window.rect = Region(0, 0, 1920, 1080)
        api.foreground_hwnd = 99
        client.refresh()
        self.assertEqual(client.size, (1920, 1080))
        self.assertFalse(client.is_foreground)
        self.assertEqual(client.to_screen((10, 20)), (10, 20))

    def test_several_clients_sorted_by_title(self):
        api = FakeWindowApi([
            FakeWindow(1, 'Tibia - Zed', OFFICIAL_EXE),
            FakeWindow(2, 'Tibia - Anna', OFFICIAL_EXE),
        ])
        self.assertEqual([c.title for c in find_client_windows(api=api)], ['Tibia - Anna', 'Tibia - Zed'])
