import pygame
import sys
import os
from pygame import mixer
import ctypes
import json
import traceback
from collections import OrderedDict
from time import time
import random


def set_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


set_dpi_awareness()
pygame.init()
mixer.init()


def get_dpi_scale():
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        return dpi / 96.0
    except Exception:
        return 1.0


DPI_SCALE = get_dpi_scale()

info = pygame.display.Info()
WIDTH = min(int(info.current_w * 0.85), 1600)
HEIGHT = min(int(info.current_h * 0.85), 900)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
pygame.display.set_caption("Spotify Free (Enhanced)")
clock = pygame.time.Clock()

BG = (18, 18, 18)
SIDEBAR = (0, 0, 0)
CARD = (30, 30, 30)
HOVER = (40, 40, 40)
GREEN = (30, 215, 96)
GREEN_H = (40, 230, 110)
GREEN_D = (25, 180, 80)
WHITE = (255, 255, 255)
GRAY = (179, 179, 179)
GRAY_D = (117, 117, 117)
GRAY_L = (200, 200, 200)
DIVIDER = (40, 40, 40)
BTN = (40, 40, 40)
BTN_H = (55, 55, 55)


def font(size, bold=False):
    scaled_size = int(size * min(DPI_SCALE, 1.2))
    try:
        return pygame.font.SysFont("Segoe UI,Arial,Helvetica", scaled_size, bold)
    except Exception:
        return pygame.font.SysFont("Arial", scaled_size, bold)


F_LOGO = font(26, True)
F_HEAD = font(36, True)
F_SUB = font(16, True)
F_BODY = font(14)
F_BOLD = font(14, True)
F_SMALL = font(12)
F_TINY = font(11)


def format_time(sec):
    try:
        return f"{int(sec // 60)}:{int(sec % 60):02d}"
    except Exception:
        return "0:00"


REPEAT_OFF, REPEAT_ALL, REPEAT_ONE = 0, 1, 2

APP_DIR = os.path.dirname(__file__) if os.path.dirname(__file__) else os.getcwd()
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
PLAYLIST_FILE = os.path.join(APP_DIR, "playlists.json")
HISTORY_FILE = os.path.join(APP_DIR, "history.json")

DEFAULT_SETTINGS = {
    "music_folder": os.path.join(APP_DIR, "music"),
    "volume": 0.7,
    "repeat_mode": REPEAT_OFF,
    "last_open_playlist": None,
    "mini_player": False
}


def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in data:
                        data[k] = v
                return data
    except (json.JSONDecodeError, IOError) as e:
        print("Failed to load settings:", e)
    return DEFAULT_SETTINGS.copy()


def save_settings():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except IOError as e:
        print("Failed to save settings:", e)


settings = load_settings()


def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return []


def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(play_history[-50:], f, indent=2)
    except IOError:
        pass


play_history = load_history()


def log_exception(msg=None):
    print("Exception:", msg)
    traceback.print_exc()


def find_music_folders():
    potential_folders = []
    music_folder_names = ["music", "Music", "songs", "Songs", "audio", "Audio", "tracks", "Tracks"]

    for name in music_folder_names:
        folder_path = os.path.join(APP_DIR, name)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            try:
                files = os.listdir(folder_path)
                if any(f.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')) for f in files):
                    potential_folders.append(folder_path)
            except (PermissionError, OSError):
                pass

    parent_dir = os.path.dirname(APP_DIR)
    for name in music_folder_names:
        folder_path = os.path.join(parent_dir, name)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            try:
                files = os.listdir(folder_path)
                if any(f.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')) for f in files):
                    potential_folders.append(folder_path)
            except (PermissionError, OSError):
                pass

    try:
        for item in os.listdir(APP_DIR):
            item_path = os.path.join(APP_DIR, item)
            if os.path.isdir(item_path):
                for name in music_folder_names:
                    subfolder = os.path.join(item_path, name)
                    if os.path.exists(subfolder) and os.path.isdir(subfolder):
                        try:
                            files = os.listdir(subfolder)
                            if any(f.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')) for f in files):
                                potential_folders.append(subfolder)
                        except (PermissionError, OSError):
                            pass
    except (PermissionError, OSError):
        pass

    return potential_folders


music_folder = settings.get("music_folder", DEFAULT_SETTINGS["music_folder"])
try:
    folder_exists = os.path.exists(music_folder)
    has_audio = False
    if folder_exists:
        has_audio = any(f.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')) for f in os.listdir(music_folder) if
                        os.path.isfile(os.path.join(music_folder, f)))
except (PermissionError, OSError):
    folder_exists = False
    has_audio = False

if not folder_exists or not has_audio:
    print("ðŸ” Music folder not found or empty, auto-searching...")
    found_folders = find_music_folders()
    if found_folders:
        best_folder = max(found_folders, key=lambda f: len(
            [x for x in os.listdir(f) if x.lower().endswith(('.mp3', '.wav', '.ogg', '.flac'))]))
        music_folder = best_folder
        settings["music_folder"] = best_folder
        save_settings()
        print(f"âœ“ Auto-detected music folder: {best_folder}")
    else:
        try:
            os.makedirs(music_folder, exist_ok=True)
            print(f"ðŸ“ Created default music folder: {music_folder}")
        except OSError as e:
            print("Could not create music folder:", e)


def scan_music_folder(folder):
    lib = []
    try:
        files = os.listdir(folder)
    except (FileNotFoundError, PermissionError) as e:
        print("Music folder not accessible:", e)
        return lib

    for f in files:
        if f.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
            path = os.path.join(folder, f)
            title = os.path.splitext(f)[0]
            artist = "Unknown"
            duration = "3:30"
            try:
                from mutagen.mp3 import MP3
                from mutagen.id3 import ID3
                audio = MP3(path, ID3=ID3)
                if audio.info and getattr(audio.info, "length", None):
                    duration = format_time(int(audio.info.length))
                if audio.tags:
                    if 'TPE1' in audio.tags:
                        artist = str(audio.tags['TPE1'])
                    if 'TIT2' in audio.tags:
                        title = str(audio.tags['TIT2'])
            except (ImportError, Exception) as e:
                print(f"Warning: couldn't read metadata for {path}: {e}")
            lib.append({
                "title": title,
                "artist": artist,
                "duration": duration,
                "file": path,
                "id": path
            })
    lib.sort(key=lambda x: x["title"].lower())
    return lib


music_library = scan_music_folder(music_folder)
if not music_library:
    music_library = [
        {"title": "Drop audio files", "artist": "in /music folder", "duration": "0:00", "file": None, "id": "demo_0"},
    ]


def load_playlists():
    try:
        if os.path.exists(PLAYLIST_FILE):
            with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except (json.JSONDecodeError, IOError) as e:
        print("Failed to load playlists:", e)
    return {"Liked Songs": [], "My Playlist": [], "Chill": []}


def save_playlists():
    try:
        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(playlists, f, indent=2)
    except IOError as e:
        print("Failed to save playlists:", e)


playlists = load_playlists()

current_index = None
is_playing = False
volume = settings.get("volume", 0.7)
mixer.music.set_volume(volume)
progress = 0.0
progress_max = 100.0
progress_timer = pygame.time.get_ticks()
shuffle_mode = False
repeat_mode = settings.get("repeat_mode", REPEAT_OFF)

current_view = "library"
search_query = ""
search_active = False
selected_playlist = settings.get("last_open_playlist", None)
scroll_offset = 0.0
scroll_velocity = 0.0
max_scroll = 0.0
hover_track = None
dragging_progress = False
dragging_volume = False

show_playlist_popup = False
popup_track_idx = None
playlist_popup_buttons = []
show_create_playlist_popup = False
new_playlist_name = ""
show_shortcuts = False
mini_player_mode = settings.get("mini_player", False)

SIDEBAR_W = 260
HEADER_H = 140
PLAYER_H = 100
TRACK_H = 56

dragging_queue_item = None
drag_start_pos = None
drag_offset = 0


class AlbumArtCache:
    def __init__(self, max_items=64, thumb_size=64):
        self.cache = OrderedDict()
        self.max_items = max_items
        self.thumb_size = thumb_size

    def get(self, track_path):
        if not track_path:
            return None
        if track_path in self.cache:
            surf = self.cache.pop(track_path)
            self.cache[track_path] = surf
            return surf
        surf = self._load_art(track_path)
        if surf:
            self.cache[track_path] = surf
            while len(self.cache) > self.max_items:
                self.cache.popitem(last=False)
        return surf

    def _load_art(self, path):
        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, APIC
            from io import BytesIO
            audio = MP3(path, ID3=ID3)
            if audio.tags:
                for tag in audio.tags.values():
                    try:
                        if tag.FrameID == 'APIC' or getattr(tag, '__class__', None).__name__ == 'APIC':
                            data = getattr(tag, 'data', None) or getattr(tag, 'data', None)
                            if data:
                                bytes_io = BytesIO(data)
                                img = pygame.image.load(bytes_io).convert_alpha()
                                img = pygame.transform.smoothscale(img, (self.thumb_size, self.thumb_size))
                                return img
                    except Exception:
                        continue
        except (ImportError, Exception):
            pass
        return None


album_cache = AlbumArtCache(max_items=96, thumb_size=40)

play_queue = []


def queue_add(track_id, play_next=False):
    if track_id is None:
        return
    if play_next and play_queue:
        play_queue.insert(0, track_id)
    else:
        play_queue.append(track_id)


def queue_pop_next():
    if play_queue:
        return play_queue.pop(0)
    return None


def queue_remove_at(index):
    if 0 <= index < len(play_queue):
        play_queue.pop(index)


def queue_move(from_idx, to_idx):
    if 0 <= from_idx < len(play_queue) and 0 <= to_idx < len(play_queue):
        item = play_queue.pop(from_idx)
        play_queue.insert(to_idx, item)


class Button:
    def __init__(self, rect, color, hover_color, text="", font_obj=None, text_color=WHITE, radius=8, active=False,
                 active_color=None):
        self.rect = pygame.Rect(rect)
        self.color = color
        self.hover_color = hover_color
        self.text = text
        self.font = font_obj or F_BODY
        self.text_color = text_color
        self.radius = radius
        self.hovered = False
        self.active = active
        self.active_color = active_color or GREEN

    def update(self, mouse_pos, active=None):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if active is not None:
            self.active = active

    def draw(self, surf):
        if self.active:
            color = self.active_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.color

        pygame.draw.rect(surf, color, self.rect, border_radius=self.radius)

        if self.text:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_x = self.rect.centerx - text_surf.get_width() // 2
            text_y = self.rect.centery - text_surf.get_height() // 2
            surf.blit(text_surf, (text_x, text_y))

    def handle_click(self, pos):
        return self.rect.collidepoint(pos)


class NavButton:
    def __init__(self, rect, text, view):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.view = view
        self.hovered = False
        self.active = False

    def update(self, mouse_pos, active=False):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.active = active

    def draw(self, surf):
        color = GREEN if self.active else (BTN_H if self.hovered else SIDEBAR)

        if color != SIDEBAR:
            pygame.draw.rect(surf, color, self.rect, border_radius=12)

        text_color = WHITE if self.active or self.hovered else GRAY
        text_surf = F_BOLD.render(self.text, True, text_color)
        surf.blit(text_surf, (self.rect.x + 16, self.rect.centery - text_surf.get_height() // 2))

        if self.active:
            active_bar = pygame.Rect(self.rect.x + 2, self.rect.y + 4, 3, self.rect.height - 8)
            pygame.draw.rect(surf, GREEN, active_bar, border_radius=2)

    def handle_click(self, pos):
        return self.rect.collidepoint(pos)


class PlaylistButton:
    def __init__(self, rect, name, count):
        self.rect = pygame.Rect(rect)
        self.name = name
        self.count = count
        self.hovered = False
        self.active = False

    def update(self, mouse_pos, active=False):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.active = active

    def draw(self, surf):
        if self.hovered or self.active:
            pygame.draw.rect(surf, BTN_H if self.hovered else BTN, self.rect, border_radius=12)

        col = GREEN if self.active else (WHITE if self.hovered else GRAY_L)
        title = F_BOLD.render(self.name, True, col)
        surf.blit(title, (self.rect.x + 16, self.rect.y + 12))

        cnt = F_SMALL.render(f"{self.count} songs", True, GRAY_D)
        surf.blit(cnt, (self.rect.x + 16, self.rect.y + 32))

        if self.active:
            active_bar = pygame.Rect(self.rect.x + 2, self.rect.y + 4, 3, self.rect.height - 8)
            pygame.draw.rect(surf, GREEN, active_bar, border_radius=2)

    def handle_click(self, pos):
        return self.rect.collidepoint(pos)


class TrackRow:
    def __init__(self, rect, track, track_id, positions, track_index):
        self.rect = pygame.Rect(rect)
        self.track = track
        self.track_id = track_id
        self.positions = positions
        self.track_index = track_index
        self.hovered = False
        self.is_current = False
        self.add_button = None
        self.thumb_surf = None
        self.title_surf = None
        self.artist_surf = None
        self.duration_surf = None
        self.number_surf = None

    def update(self, mouse_pos, current_idx):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.is_current = self.track_id == current_idx

        if self.hovered:
            add_rect = pygame.Rect(self.rect.right - 210, self.rect.y + 14, 100, 28)
            extra_rect = pygame.Rect(self.rect.right - 102, self.rect.y + 14, 80, 28)
            if current_view == "playlist" and selected_playlist:
                self.add_button = Button(add_rect, (150, 50, 50), (180, 60, 60), "Remove", F_SMALL, WHITE, 16)
                self.queue_button = Button(extra_rect, BTN, BTN_H, "Play Next", F_SMALL, WHITE, 16)
                self.queue_button.update(mouse_pos)
            else:
                self.add_button = Button(add_rect, BTN, BTN_H, "Add", F_SMALL, WHITE, 16)
                self.queue_button = Button(extra_rect, BTN, BTN_H, "Play Next", F_SMALL, WHITE, 16)
            self.add_button.update(mouse_pos)
        else:
            self.add_button = None
            self.queue_button = None

    def draw(self, surf):
        if self.hovered:
            pygame.draw.rect(surf, HOVER, self.rect, border_radius=12)

        thumb_size = 40
        thumb_x = self.positions[0] - 50
        thumb_rect = pygame.Rect(thumb_x, self.rect.centery - thumb_size // 2, thumb_size, thumb_size)

        if not self.thumb_surf:
            self.thumb_surf = album_cache.get(self.track.get("file"))
            if not self.thumb_surf:
                surf_temp = pygame.Surface((thumb_size, thumb_size))
                for i in range(thumb_size):
                    ratio = i / thumb_size
                    color = (int(60 + ratio * 80), int(40 + ratio * 100), int(80 + ratio * 60))
                    pygame.draw.rect(surf_temp, color, (0, i, thumb_size, 1))
                pygame.draw.circle(surf_temp, (220, 220, 220), (thumb_size // 2 - 4, thumb_size // 2 + 6), 4, 2)
                pygame.draw.circle(surf_temp, (220, 220, 220), (thumb_size // 2 + 6, thumb_size // 2 + 4), 4, 2)
                pygame.draw.line(surf_temp, (220, 220, 220), (thumb_size // 2 + 2, thumb_size // 2 + 4),
                                 (thumb_size // 2 + 2, thumb_size // 2 - 8), 2)
                self.thumb_surf = surf_temp

        surf.blit(self.thumb_surf, thumb_rect)

        nc = GREEN if self.is_current else GRAY_D
        if self.is_current and is_playing:
            x = self.positions[0]
            y = self.rect.centery
            bar_width = 3
            bar_spacing = 2
            time_factor = pygame.time.get_ticks() / 100
            for i in range(3):
                height = 8 + 6 * abs(((time_factor + i * 30) % 100) / 50 - 1)
                pygame.draw.rect(surf, GREEN, (x + i * (bar_width + bar_spacing), y - height / 2, bar_width, height),
                                 border_radius=1)
        else:
            if not self.number_surf:
                nt = str(self.track_index + 1)
                self.number_surf = F_SMALL.render(nt, True, nc)
            surf.blit(self.number_surf, (self.positions[0], self.rect.centery - self.number_surf.get_height() // 2))

        if not self.title_surf:
            self.title_surf = F_BODY.render(self.track["title"][:35], True, WHITE)
        if self.is_current:
            title_display = F_BODY.render(self.track["title"][:35], True, GREEN)
        else:
            title_display = self.title_surf
        surf.blit(title_display, (self.positions[1], self.rect.centery - title_display.get_height() // 2))

        if not self.artist_surf:
            self.artist_surf = F_BODY.render(self.track["artist"][:30], True, GRAY)
        surf.blit(self.artist_surf, (self.positions[2], self.rect.centery - self.artist_surf.get_height() // 2))

        if not self.duration_surf:
            self.duration_surf = F_BODY.render(self.track["duration"], True, GRAY)
        surf.blit(self.duration_surf, (self.positions[3], self.rect.centery - self.duration_surf.get_height() // 2))

        if self.add_button:
            self.add_button.draw(surf)
        if getattr(self, "queue_button", None):
            self.queue_button.draw(surf)

    def handle_click(self, pos):
        if getattr(self, "queue_button", None) and self.queue_button.handle_click(pos):
            return "queue_next"
        if self.add_button and self.add_button.handle_click(pos):
            if current_view == "playlist" and selected_playlist:
                return "remove_playlist"
            else:
                return "add_playlist"
        elif self.rect.collidepoint(pos):
            return "play"
        return None


class SearchBox:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.active = False
        self.hovered = False

    def update(self, mouse_pos, active):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.active = active

    def draw(self, surf, query):
        bg = BTN_H if self.active or self.hovered else BTN
        pygame.draw.rect(surf, bg, self.rect, border_radius=24)

        icon_x, icon_y = self.rect.x + 20, self.rect.centery
        pygame.draw.circle(surf, GRAY_D, (icon_x, icon_y - 1), 6, 2)
        pygame.draw.line(surf, GRAY_D, (icon_x + 4, icon_y + 3), (icon_x + 7, icon_y + 6), 2)

        txt = query if query else "What do you want to listen to?"
        col = WHITE if query else GRAY_D
        t = F_BODY.render(txt[:50], True, col)
        surf.blit(t, (self.rect.x + 40, self.rect.centery - t.get_height() // 2))

        if self.active and pygame.time.get_ticks() % 1000 < 500:
            crx = self.rect.x + 40 + t.get_width() + 3
            pygame.draw.line(surf, WHITE, (crx, self.rect.y + 12), (crx, self.rect.y + 28), 2)

    def handle_click(self, pos):
        return self.rect.collidepoint(pos)


class CircleButton:
    def __init__(self, center, radius, icon, color=WHITE):
        self.center = center
        self.radius = radius
        self.icon = icon
        self.color = color
        self.hovered = False

    def update(self, mouse_pos):
        dx = mouse_pos[0] - self.center[0]
        dy = mouse_pos[1] - self.center[1]
        self.hovered = (dx * dx + dy * dy) <= (self.radius * self.radius)

    def draw(self, surf):
        color = WHITE if self.hovered else self.color

        if self.icon == "play":
            points = [(self.center[0] - 6, self.center[1] - 8), (self.center[0] - 6, self.center[1] + 8),
                      (self.center[0] + 8, self.center[1])]
            pygame.draw.polygon(surf, color, points)
        elif self.icon == "pause":
            pygame.draw.rect(surf, color, (self.center[0] - 6, self.center[1] - 7, 4, 14), border_radius=1)
            pygame.draw.rect(surf, color, (self.center[0] + 2, self.center[1] - 7, 4, 14), border_radius=1)
        elif self.icon == "prev" or self.icon == "next":
            if self.icon == "prev":
                pygame.draw.rect(surf, color, (self.center[0] - 8, self.center[1] - 6, 2, 12), border_radius=1)
                points = [(self.center[0] + 6, self.center[1] - 6), (self.center[0] + 6, self.center[1] + 6),
                          (self.center[0] - 3, self.center[1])]
            else:
                pygame.draw.rect(surf, color, (self.center[0] + 6, self.center[1] - 6, 2, 12), border_radius=1)
                points = [(self.center[0] - 6, self.center[1] - 6), (self.center[0] - 6, self.center[1] + 6),
                          (self.center[0] + 3, self.center[1])]
            pygame.draw.polygon(surf, color, points)
        elif self.icon == "shuffle":
            pygame.draw.line(surf, color, (self.center[0] - 6, self.center[1] - 4),
                             (self.center[0] + 6, self.center[1] + 4), 2)
            pygame.draw.line(surf, color, (self.center[0] - 6, self.center[1] + 4),
                             (self.center[0] + 6, self.center[1] - 4), 2)
        elif self.icon == "repeat":
            pygame.draw.arc(surf, color, (self.center[0] - 6, self.center[1] - 6, 12, 12), 0.5, 5.5, 2)
            pygame.draw.polygon(surf, color,
                                [(self.center[0] + 6, self.center[1] - 6), (self.center[0] + 6, self.center[1] - 2),
                                 (self.center[0] + 9, self.center[1] - 6)])
            if repeat_mode == REPEAT_ONE:
                one_surf = F_TINY.render("1", True, color)
                surf.blit(one_surf,
                          (self.center[0] - one_surf.get_width() // 2, self.center[1] - one_surf.get_height() // 2))

    def handle_click(self, pos):
        dx = pos[0] - self.center[0]
        dy = pos[1] - self.center[1]
        return (dx * dx + dy * dy) <= (self.radius * self.radius)


class Slider:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.hovered = False
        self.dragging = False
        self.value = 0.0

    def update(self, mouse_pos, value, dragging):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.value = value
        self.dragging = dragging

    def draw(self, surf):
        bar_height = 4
        bar_rect = pygame.Rect(self.rect.x, self.rect.centery - bar_height // 2, self.rect.width, bar_height)
        pygame.draw.rect(surf, BTN, bar_rect, border_radius=2)

        fill_width = int(self.rect.width * self.value)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.centery - bar_height // 2, fill_width, bar_height)
            pygame.draw.rect(surf, GREEN, fill_rect, border_radius=2)

        handle_x = self.rect.x + fill_width
        if self.hovered or self.dragging:
            glow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (30, 215, 96, 30), (10, 10), 10)
            surf.blit(glow_surf, (handle_x - 10, self.rect.centery - 10))
            pygame.draw.circle(surf, WHITE, (handle_x, self.rect.centery), 6)
            pygame.draw.circle(surf, GREEN, (handle_x, self.rect.centery), 4)
        else:
            pygame.draw.circle(surf, WHITE, (handle_x, self.rect.centery), 5)

    def handle_click(self, pos):
        return self.rect.collidepoint(pos)

    def get_value_at_pos(self, x):
        return max(0.0, min(1.0, (x - self.rect.x) / self.rect.width))


def render_text(text, font_obj, color, antialias=True):
    cache_key = (text, font_obj, color)
    if not hasattr(render_text, 'cache'):
        render_text.cache = {}
    if cache_key not in render_text.cache:
        render_text.cache[cache_key] = font_obj.render(text, True, color)
    return render_text.cache[cache_key]


def get_library():
    if current_view == "search" and search_query:
        return [t for t in music_library if
                search_query.lower() in t["title"].lower() or search_query.lower() in t["artist"].lower()]
    elif current_view == "playlist" and selected_playlist:
        result = []
        for song_id in playlists.get(selected_playlist, []):
            track = next((t for t in music_library if t["id"] == song_id), None)
            if track:
                result.append(track)
        return result
    elif current_view == "history":
        result = []
        for song_id in reversed(play_history[-50:]):
            track = next((t for t in music_library if t["id"] == song_id), None)
            if track and track not in result:
                result.append(track)
        return result
    return music_library


def add_to_playlist(song_id, pname):
    if not pname:
        return
    if pname in playlists:
        if song_id not in playlists[pname]:
            playlists[pname].append(song_id)
            save_playlists()


def remove_from_playlist(song_id, pname):
    if not pname:
        return
    if pname in playlists and song_id in playlists[pname]:
        playlists[pname].remove(song_id)
        save_playlists()


playlist_context_menu = {"visible": False, "playlist": None, "pos": (0, 0), "rects": {}}
confirm_delete = {"visible": False, "playlist": None, "yes_rect": None, "no_rect": None}


def draw_playlist_context_menu(surf, mouse_pos):
    if not playlist_context_menu["visible"] or not playlist_context_menu["playlist"]:
        return
    mx, my = playlist_context_menu["pos"]
    menu_w = 170
    menu_h = 80
    if mx + menu_w > WIDTH:
        mx = WIDTH - menu_w - 10
    if my + menu_h > HEIGHT:
        my = HEIGHT - menu_h - 10
    rect = pygame.Rect(mx, my, menu_w, menu_h)
    shadow = rect.copy();
    shadow.x += 4;
    shadow.y += 4
    pygame.draw.rect(surf, (0, 0, 0), shadow, border_radius=12)
    pygame.draw.rect(surf, CARD, rect, border_radius=12)
    title = F_SUB.render(playlist_context_menu["playlist"], True, WHITE)
    surf.blit(title, (rect.x + 12, rect.y + 8))
    opt1 = pygame.Rect(rect.x + 8, rect.y + 34, rect.width - 16, 20)
    opt2 = pygame.Rect(rect.x + 8, rect.y + 56, rect.width - 16, 20)
    playlist_context_menu["rects"] = {"open": opt1, "delete": opt2, "rect": rect}
    mp = mouse_pos
    for r in (opt1, opt2):
        if r.collidepoint(mp):
            pygame.draw.rect(surf, BTN_H, r, border_radius=8)
    otext = F_BODY.render("Open Playlist", True, WHITE)
    dtext = F_BODY.render("Delete Playlist", True, WHITE)
    surf.blit(otext, (opt1.x + 8, opt1.y))
    surf.blit(dtext, (opt2.x + 8, opt2.y))


def draw_confirm_delete(surf, mouse_pos):
    if not confirm_delete["visible"] or not confirm_delete["playlist"]:
        return
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    surf.blit(overlay, (0, 0))
    popup_w = 420
    popup_h = 160
    popup_x = WIDTH // 2 - popup_w // 2
    popup_y = HEIGHT // 2 - popup_h // 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
    shadow = popup_rect.copy();
    shadow.x += 4;
    shadow.y += 4
    pygame.draw.rect(surf, (0, 0, 0), shadow, border_radius=12)
    pygame.draw.rect(surf, CARD, popup_rect, border_radius=12)
    title = F_HEAD.render("Delete Playlist?", True, WHITE)
    surf.blit(title, (popup_x + 24, popup_y + 16))
    txt = F_BODY.render(f"Are you sure you want to delete '{confirm_delete['playlist']}'?", True, GRAY)
    surf.blit(txt, (popup_x + 24, popup_y + 72))
    yes_rect = pygame.Rect(popup_x + popup_w - 240, popup_y + popup_h - 60, 96, 36)
    no_rect = pygame.Rect(popup_x + popup_w - 120, popup_y + popup_h - 60, 96, 36)
    confirm_delete["yes_rect"] = yes_rect
    confirm_delete["no_rect"] = no_rect
    yes_hover = yes_rect.collidepoint(mouse_pos)
    no_hover = no_rect.collidepoint(mouse_pos)
    pygame.draw.rect(surf, GREEN_H if yes_hover else GREEN, yes_rect, border_radius=18)
    pygame.draw.rect(surf, BTN_H if no_hover else BTN, no_rect, border_radius=18)
    ytxt = F_BOLD.render("Yes, delete", True, WHITE)
    ntxt = F_BOLD.render("Cancel", True, WHITE)
    surf.blit(ytxt, (yes_rect.centerx - ytxt.get_width() // 2, yes_rect.centery - ytxt.get_height() // 2))
    surf.blit(ntxt, (no_rect.centerx - ntxt.get_width() // 2, no_rect.centery - ntxt.get_height() // 2))


def draw_shortcuts(surf):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    surf.blit(overlay, (0, 0))

    popup_w = 500
    popup_h = 450
    popup_x = WIDTH // 2 - popup_w // 2
    popup_y = HEIGHT // 2 - popup_h // 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)

    shadow = popup_rect.copy()
    shadow.x += 4
    shadow.y += 4
    pygame.draw.rect(surf, (0, 0, 0), shadow, border_radius=12)
    pygame.draw.rect(surf, CARD, popup_rect, border_radius=12)

    title = F_HEAD.render("Keyboard Shortcuts", True, WHITE)
    surf.blit(title, (popup_x + 24, popup_y + 20))

    shortcuts = [
        ("Space", "Play/Pause"),
        ("â†’ (Right Arrow)", "Next Track"),
        ("â† (Left Arrow)", "Previous Track"),
        ("S", "Toggle Shuffle"),
        ("R", "Cycle Repeat Mode"),
        ("M", "Toggle Mini Player"),
        ("K", "Show Shortcuts"),
        ("/", "Focus Search"),
        ("Esc", "Close Popups/Quit")
    ]

    y = popup_y + 80
    for key, action in shortcuts:
        key_rect = pygame.Rect(popup_x + 30, y, 180, 32)
        pygame.draw.rect(surf, BTN, key_rect, border_radius=8)
        key_text = F_BODY.render(key, True, WHITE)
        surf.blit(key_text, (key_rect.x + 12, key_rect.centery - key_text.get_height() // 2))

        action_text = F_BODY.render(action, True, GRAY_L)
        surf.blit(action_text, (popup_x + 230, y + 8))

        y += 40

    close_text = F_SMALL.render("Press K or Esc to close", True, GRAY)
    surf.blit(close_text, (popup_x + popup_w // 2 - close_text.get_width() // 2, popup_y + popup_h - 30))


nav_buttons = []
playlist_buttons = []
track_rows = []
search_box = None
control_buttons = {}
progress_slider = None
volume_slider = None
scrollbar_rect = None
dragging_scrollbar = False


def create_sidebar_ui():
    global nav_buttons, playlist_buttons
    nav_buttons = []
    y = 90
    nav = [("Home", "library"), ("Search", "search"), ("Your Library", "library"), ("Queue", "queue"),
           ("History", "history"), ("Settings", "settings")]
    for label, view in nav:
        rect = pygame.Rect(16, y, SIDEBAR_W - 32, 40)
        btn = NavButton(rect, label, view)
        nav_buttons.append(btn)
        y += 44
    y += 30
    playlist_buttons = []
    for pname, tracks in playlists.items():
        rect = pygame.Rect(16, y, SIDEBAR_W - 32, 56)
        btn = PlaylistButton(rect, pname, len(tracks))
        playlist_buttons.append(btn)
        y += 60


create_sidebar_ui()


def draw_sidebar(surf, mp):
    pygame.draw.rect(surf, SIDEBAR, (0, 0, SIDEBAR_W, HEIGHT))
    logo = render_text("Spotify Free", F_LOGO, WHITE)
    surf.blit(logo, (20, 28))
    for btn in nav_buttons:
        active = (btn.view == current_view and not selected_playlist) or (btn.view == "playlist" and selected_playlist)
        btn.update(mp, active)
        btn.draw(surf)
    y = 90 + (44 * 6) + 10
    pygame.draw.line(surf, DIVIDER, (20, y - 15), (SIDEBAR_W - 20, y - 15), 1)
    for btn in playlist_buttons:
        active = current_view == "playlist" and selected_playlist == btn.name
        btn.count = len(playlists.get(btn.name, []))
        btn.update(mp, active)
        btn.draw(surf)


def draw_content(surf, mp):
    global scroll_offset, max_scroll, track_rows, search_box, scrollbar_rect
    cx = SIDEBAR_W
    cw = WIDTH - SIDEBAR_W
    for i in range(HEADER_H):
        color = (BG[0] + int((GREEN_D[0] - BG[0]) * (1 - i / HEADER_H) * 0.3),
                 BG[1] + int((GREEN_D[1] - BG[1]) * (1 - i / HEADER_H) * 0.3),
                 BG[2] + int((GREEN_D[2] - BG[2]) * (1 - i / HEADER_H) * 0.3))
        pygame.draw.line(surf, color, (cx, i), (cx + cw, i))
    if current_view == "search":
        title = "Search"
    elif current_view == "playlist" and selected_playlist:
        title = selected_playlist
    elif current_view == "settings":
        title = "Settings"
    elif current_view == "queue":
        title = "Queue"
    elif current_view == "history":
        title = "Recently Played"
    else:
        title = "Your Library"
    ttl = render_text(title, F_HEAD, WHITE)
    surf.blit(ttl, (cx + 32, 40))
    if current_view == "search":
        sx, sy, sw, sh = cx + 32, 95, min(500, cw - 64), 48
        if not search_box or search_box.rect != pygame.Rect(sx, sy, sw, sh):
            search_box = SearchBox((sx, sy, sw, sh))
        search_box.update(mp, search_active)
        search_box.draw(surf, search_query)
    else:
        search_box = None
        lib = get_library()
        inf = render_text(f"{len(lib)} songs", F_SUB, GRAY_D)
        surf.blit(inf, (cx + 32, 95))
    if current_view == "settings":
        draw_settings_page(surf, mp, cx, cw)
        return
    if current_view == "queue":
        draw_queue_page(surf, mp, cx, cw)
        return
    list_y = HEADER_H + 20
    list_h = HEIGHT - PLAYER_H - list_y - 10
    headers = ["#", "TITLE", "ARTIST", "DURATION"]
    positions = [cx + 110, cx + 160, cx + cw - 380, cx + cw - 140]
    for h, x in zip(headers, positions):
        t = render_text(h, F_TINY, GRAY_D)
        surf.blit(t, (x, list_y))
    pygame.draw.line(surf, DIVIDER, (cx + 32, list_y + 24), (cx + cw - 32, list_y + 24), 1)
    list_cy = list_y + 36
    scroll_area = pygame.Rect(cx, list_cy, cw, list_h - 36)
    surf.set_clip(scroll_area)
    lib = get_library()
    content_h = len(lib) * TRACK_H
    max_scroll = max(0, content_h - list_h + 36)
    y = list_cy - scroll_offset
    track_rows = []
    for i, track in enumerate(lib):
        if y < list_cy - TRACK_H or y > list_cy + list_h:
            track_rows.append(None)
            y += TRACK_H
            continue
        rect = pygame.Rect(cx + 32, y, cw - 64, TRACK_H - 4)
        track_row = TrackRow(rect, track, track["id"], positions, i)
        track_row.update(mp, current_index)
        track_row.draw(surf)
        track_rows.append(track_row)
        y += TRACK_H
    surf.set_clip(None)
    scrollbar_rect = None
    if max_scroll > 0:
        bar_h = max(50, int(list_h * (list_h / content_h))) if content_h > 0 else max(50, list_h)
        bar_y = list_cy + int((scroll_offset / max_scroll) * (list_h - bar_h)) if max_scroll > 0 else list_cy
        scrollbar_rect = pygame.Rect(cx + cw - 12, bar_y, 4, bar_h)
        scrollbar_hovered = scrollbar_rect.collidepoint(mp) or dragging_scrollbar
        color = GRAY_L if scrollbar_hovered else GRAY_D
        width = 6 if scrollbar_hovered else 4
        scrollbar_rect = pygame.Rect(cx + cw - 12, bar_y, width, bar_h)
        pygame.draw.rect(surf, color, scrollbar_rect, border_radius=3)


def draw_settings_page(surf, mp, cx, cw):
    section_x = cx + 32
    y = 120
    label = F_SUB.render("Music Folder", True, WHITE)
    surf.blit(label, (section_x, y))
    y += 30
    folder_rect = pygame.Rect(section_x, y, min(500, cw - 100), 36)
    pygame.draw.rect(surf, BTN, folder_rect, border_radius=12)
    folder_text = F_BODY.render(settings.get("music_folder", ""), True, GRAY_L)
    surf.blit(folder_text, (folder_rect.x + 10, folder_rect.centery - folder_text.get_height() // 2))
    y += 56
    vol_label = F_SUB.render("Default Volume", True, WHITE)
    surf.blit(vol_label, (section_x, y))
    y += 30
    vol_rect = pygame.Rect(section_x, y, 300, 20)
    pygame.draw.rect(surf, BTN, vol_rect, border_radius=10)
    fill = int(vol_rect.width * settings.get("volume", 0.7))
    if fill > 0:
        fill_rect = pygame.Rect(vol_rect.x, vol_rect.y, fill, vol_rect.height)
        pygame.draw.rect(surf, GREEN, fill_rect, border_radius=10)
    vol_text = F_BODY.render(f"{int(settings.get('volume', 0.7) * 100)}%", True, GRAY)
    surf.blit(vol_text, (vol_rect.x + vol_rect.width + 12, vol_rect.y - 3))
    y += 56
    rep_label = F_SUB.render("Repeat Mode", True, WHITE)
    surf.blit(rep_label, (section_x, y))
    y += 30
    btn_w = 120
    names = [("Off", REPEAT_OFF), ("All", REPEAT_ALL), ("One", REPEAT_ONE)]
    bx = section_x
    rects = []
    for nm, val in names:
        r = pygame.Rect(bx, y, btn_w, 34)
        hovered = r.collidepoint(mp)
        active = (settings.get("repeat_mode", REPEAT_OFF) == val)
        pygame.draw.rect(surf, GREEN if active else (BTN_H if hovered else BTN), r, border_radius=17)
        txt = F_BODY.render(nm, True, WHITE)
        surf.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))
        rects.append((r, val))
        bx += btn_w + 12
    y += 56
    mini_label = F_SUB.render("Mini Player Mode", True, WHITE)
    surf.blit(mini_label, (section_x, y))
    y += 30
    mini_rect = pygame.Rect(section_x, y, 80, 34)
    mini_hovered = mini_rect.collidepoint(mp)
    mini_active = settings.get("mini_player", False)
    pygame.draw.rect(surf, GREEN if mini_active else (BTN_H if mini_hovered else BTN), mini_rect, border_radius=17)
    mini_txt = F_BODY.render("Toggle", True, WHITE)
    surf.blit(mini_txt, (mini_rect.centerx - mini_txt.get_width() // 2, mini_rect.centery - mini_txt.get_height() // 2))
    y += 56
    save_txt = F_SMALL.render("Settings auto-saved when you change them.", True, GRAY)
    surf.blit(save_txt, (section_x, y))

    y += 80
    pygame.draw.line(surf, DIVIDER, (section_x, y), (section_x + min(500, cw - 100), y), 1)
    y += 40

    credits_title = F_SUB.render("Credits", True, WHITE)
    surf.blit(credits_title, (section_x, y))
    y += 30

    made_by = F_BODY.render("Made by Aarush Mishra", True, GRAY_L)
    surf.blit(made_by, (section_x, y))
    y += 28

    made_with = F_BODY.render("Made with Python and Love", True, GRAY_L)
    surf.blit(made_with, (section_x, y))

    heart_x = section_x + made_with.get_width() + 8
    heart_y = y - 2
    pygame.draw.circle(surf, (255, 100, 100), (heart_x + 4, heart_y + 4), 3)
    pygame.draw.circle(surf, (255, 100, 100), (heart_x + 9, heart_y + 4), 3)
    points = [(heart_x + 1, heart_y + 6), (heart_x + 6.5, heart_y + 11), (heart_x + 12, heart_y + 6)]
    pygame.draw.polygon(surf, (255, 100, 100), points)

    draw_settings_page._folder_rect = folder_rect
    draw_settings_page._vol_rect = vol_rect
    draw_settings_page._repeat_rects = rects
    draw_settings_page._mini_rect = mini_rect


def draw_queue_page(surf, mp, cx, cw):
    global queue_rows, scroll_offset, max_scroll, dragging_scrollbar, scroll_velocity, dragging_queue_item
    cx = SIDEBAR_W
    cw = WIDTH - SIDEBAR_W
    list_y = HEADER_H + 20
    list_h = HEIGHT - PLAYER_H - list_y - 10
    for i in range(HEADER_H):
        color = (
            BG[0] + int((GREEN_D[0] - BG[0]) * (1 - i / HEADER_H) * 0.3),
            BG[1] + int((GREEN_D[1] - BG[1]) * (1 - i / HEADER_H) * 0.3),
            BG[2] + int((GREEN_D[2] - BG[2]) * (1 - i / HEADER_H) * 0.3)
        )
        pygame.draw.line(surf, color, (cx, i), (cx + cw, i))
    title = render_text("Queue", F_HEAD, WHITE)
    surf.blit(title, (cx + 32, 40))
    headers = ["#", "TITLE", "ARTIST", "DURATION"]
    positions = [cx + 110, cx + 160, cx + cw - 380, cx + cw - 140]
    for h, x in zip(headers, positions):
        t = render_text(h, F_TINY, GRAY_D)
        surf.blit(t, (x, list_y))
    pygame.draw.line(surf, DIVIDER, (cx + 32, list_y + 24), (cx + cw - 32, list_y + 24), 1)
    visible_songs = []
    for tid in play_queue:
        track = next((t for t in music_library if t["id"] == tid), None)
        if track:
            visible_songs.append(track)
    padding = 8
    row_height = int(TRACK_H * min(DPI_SCALE, 1.2))
    content_h = max(0, len(visible_songs) * (row_height + padding))
    list_cy = list_y + 36
    max_scroll = max(0.0, content_h - (list_h - 36))
    scroll_offset = max(0.0, min(max_scroll, scroll_offset))
    if not visible_songs:
        empty_text = render_text("Queue is empty. Use 'Play Next' to add songs here.", F_BODY, GRAY)
        surf.blit(empty_text, (cx + 40, list_cy + 40))
        return
    list_rect = pygame.Rect(cx + 32, list_cy, cw - 64, list_h - 36)
    surf.set_clip(list_rect)
    y = list_cy - scroll_offset
    queue_rows = []
    draw_queue_page.rects = []
    for i, track in enumerate(visible_songs):
        rect = pygame.Rect(cx + 32, int(y), cw - 64, row_height)
        y += row_height + padding
        if rect.bottom < list_cy or rect.top > list_cy + list_rect.height:
            queue_rows.append(None)
            draw_queue_page.rects.append((None, None, None, track["id"]))
            continue
        base_col = (28, 28, 28) if i % 2 == 0 else CARD
        if dragging_queue_item == i:
            pygame.draw.rect(surf, (60, 60, 60), rect, border_radius=12)
        else:
            pygame.draw.rect(surf, base_col, rect, border_radius=12)
        is_hover = rect.collidepoint(mp)
        if is_hover and dragging_queue_item is None:
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 14))
            surf.blit(overlay, (rect.x, rect.y))
        else:
            pygame.draw.line(surf, DIVIDER, (rect.x + 8, rect.bottom - 1), (rect.right - 8, rect.bottom - 1))
        nc = GREEN if track["id"] == current_index and is_playing else GRAY_D
        idx_surf = F_SMALL.render(str(i + 1), True, nc)
        surf.blit(idx_surf, (positions[0], rect.centery - idx_surf.get_height() // 2))
        title_surf = F_BODY.render(track["title"][:45], True, WHITE if track["id"] != current_index else GREEN)
        artist_surf = F_SMALL.render(track["artist"][:36], True, GRAY)
        dur_surf = F_SMALL.render(track["duration"], True, GRAY_D)
        surf.blit(title_surf, (positions[1], rect.centery - title_surf.get_height() // 2))
        surf.blit(artist_surf, (positions[2], rect.centery - artist_surf.get_height() // 2))
        surf.blit(dur_surf, (positions[3], rect.centery - dur_surf.get_height() // 2))

        drag_rect = pygame.Rect(positions[0] - 30, rect.centery - 12, 20, 24)
        dh = drag_rect.collidepoint(mp)
        pygame.draw.rect(surf, GRAY_L if dh else GRAY_D, (drag_rect.x + 4, drag_rect.y + 6, 2, 12), border_radius=1)
        pygame.draw.rect(surf, GRAY_L if dh else GRAY_D, (drag_rect.x + 8, drag_rect.y + 6, 2, 12), border_radius=1)
        pygame.draw.rect(surf, GRAY_L if dh else GRAY_D, (drag_rect.x + 12, drag_rect.y + 6, 2, 12), border_radius=1)

        play_rect = pygame.Rect(rect.right - 150, rect.y + (rect.height - 28) // 2, 64, 28)
        rem_rect = pygame.Rect(rect.right - 80, rect.y + (rect.height - 28) // 2, 64, 28)
        ph = play_rect.collidepoint(mp)
        rh = rem_rect.collidepoint(mp)
        if ph:
            pygame.draw.rect(surf, (60, 140, 220), play_rect.inflate(4, 4), border_radius=8)
            txt = F_SMALL.render("Play", True, WHITE)
            surf.blit(txt, (play_rect.centerx - txt.get_width() // 2, play_rect.centery - txt.get_height() // 2))
        else:
            pygame.draw.rect(surf, (50, 120, 200), play_rect, border_radius=8)
            txt = F_SMALL.render("Play", True, WHITE)
            surf.blit(txt, (play_rect.centerx - txt.get_width() // 2, play_rect.centery - txt.get_height() // 2))
        if rh:
            pygame.draw.rect(surf, (180, 70, 70), rem_rect.inflate(4, 4), border_radius=8)
            txt2 = F_SMALL.render("Remove", True, WHITE)
            surf.blit(txt2, (rem_rect.centerx - txt2.get_width() // 2, rem_rect.centery - txt2.get_height() // 2))
        else:
            pygame.draw.rect(surf, (150, 50, 50), rem_rect, border_radius=8)
            txt2 = F_SMALL.render("Remove", True, WHITE)
            surf.blit(txt2, (rem_rect.centerx - txt2.get_width() // 2, rem_rect.centery - txt2.get_height() // 2))
        draw_queue_page.rects.append((rem_rect, play_rect, drag_rect, track["id"]))
        queue_rows.append(rect)
    surf.set_clip(None)
    if max_scroll > 0:
        bar_w = 6
        bar_h = max(40, int((list_rect.height / content_h) * list_rect.height)) if content_h > 0 else 40
        bar_y = list_cy + int((scroll_offset / max_scroll) * (list_rect.height - bar_h)) if max_scroll > 0 else list_cy
        bar_rect = pygame.Rect(cx + cw - 20, bar_y, bar_w, bar_h)
        hovered_bar = bar_rect.collidepoint(mp) or dragging_scrollbar
        pygame.draw.rect(surf, GRAY_D if not hovered_bar else GRAY_L, bar_rect, border_radius=4)


def draw_player(surf, mp):
    global control_buttons, progress_slider, volume_slider
    py = HEIGHT - PLAYER_H
    pygame.draw.rect(surf, CARD, (0, py, WIDTH, PLAYER_H))
    pygame.draw.line(surf, DIVIDER, (0, py), (WIDTH, py), 1)
    if current_index is not None:
        track = next((t for t in music_library if t["id"] == current_index), None)
        if track:
            art_size = 64
            art = pygame.Rect(20, py + 18, art_size, art_size)
            album_art_surf = album_cache.get(track.get("file"))
            if album_art_surf:
                surf.blit(album_art_surf, art)
            else:
                for i in range(art_size):
                    ratio = i / art_size
                    color = (int(60 + ratio * 80), int(40 + ratio * 100), int(80 + ratio * 60))
                    pygame.draw.rect(surf, color, (art.x, art.y + i, art_size, 1))
                pygame.draw.circle(surf, GRAY_L, (art.centerx - 4, art.centery + 8), 6, 2)
            pygame.draw.rect(surf, BTN, art, border_radius=6, width=2)
            ttl = render_text(track["title"][:35], F_BOLD, WHITE)
            surf.blit(ttl, (art.right + 16, py + 28))
            art_text = render_text(track["artist"][:35], F_SMALL, GRAY)
            surf.blit(art_text, (art.right + 16, py + 50))
    cx = WIDTH // 2
    cy = py + 26
    control_buttons = {
        "shuffle": CircleButton((cx - 180, cy + 10), 14, "shuffle", GREEN if shuffle_mode else GRAY),
        "prev": CircleButton((cx - 90, cy + 10), 14, "prev"),
        "play": Button(pygame.Rect(cx - 22, cy - 2, 44, 44), GREEN, GREEN_H, "", F_HEAD, WHITE, 22),
        "next": CircleButton((cx + 90, cy + 10), 14, "next"),
        "repeat": CircleButton((cx + 180, cy + 10), 14, "repeat", GREEN if repeat_mode > 0 else GRAY)
    }
    control_buttons["shuffle"].color = GREEN if shuffle_mode else GRAY
    control_buttons["repeat"].color = GREEN if repeat_mode > 0 else GRAY
    for key in ["shuffle", "prev", "next", "repeat"]:
        control_buttons[key].update(mp)
        control_buttons[key].draw(surf)
    play_btn = control_buttons["play"]
    play_btn.update(mp)
    color = GREEN_H if play_btn.hovered else GREEN
    pygame.draw.circle(surf, color, (cx, cy + 8), 22)
    if is_playing:
        pygame.draw.rect(surf, WHITE, (cx - 6, cy + 2, 4, 12), border_radius=1)
        pygame.draw.rect(surf, WHITE, (cx + 2, cy + 2, 4, 12), border_radius=1)
    else:
        points = [(cx - 4, cy + 2), (cx - 4, cy + 14), (cx + 8, cy + 8)]
        pygame.draw.polygon(surf, WHITE, points)
    bw = min(800, WIDTH - 400)
    bx = cx - bw // 2
    by = py + 70
    ct = format_time(progress)
    tt = format_time(progress_max)
    cts = render_text(ct, F_TINY, GRAY_D)
    tts = render_text(tt, F_TINY, GRAY_D)
    surf.blit(cts, (bx - 50, by - 2))
    surf.blit(tts, (bx + bw + 10, by - 2))
    progress_slider = Slider((bx, by - 6, bw, 12))
    progress_slider.update(mp, progress / progress_max if progress_max > 0 else 0, dragging_progress)
    progress_slider.draw(surf)
    vx = WIDTH - 220
    vy = py + 40
    vw = 120
    vol_icon_x = vx - 35
    if volume > 0:
        pygame.draw.polygon(surf, GRAY, [(vol_icon_x, vy - 4), (vol_icon_x, vy + 4), (vol_icon_x + 4, vy + 4),
                                         (vol_icon_x + 8, vy + 8), (vol_icon_x + 8, vy - 8), (vol_icon_x + 4, vy - 4)])
        if volume > 0.3:
            pygame.draw.arc(surf, GRAY, (vol_icon_x + 8, vy - 6, 8, 12), -0.7, 0.7, 2)
        if volume > 0.6:
            pygame.draw.arc(surf, GRAY, (vol_icon_x + 12, vy - 10, 12, 20), -0.7, 0.7, 2)
    else:
        pygame.draw.polygon(surf, GRAY, [(vol_icon_x, vy - 4), (vol_icon_x, vy + 4), (vol_icon_x + 4, vy + 4),
                                         (vol_icon_x + 8, vy + 8), (vol_icon_x + 8, vy - 8), (vol_icon_x + 4, vy - 4)])
        pygame.draw.line(surf, GRAY, (vol_icon_x + 10, vy - 6), (vol_icon_x + 18, vy + 6), 2)
    volume_slider = Slider((vx, vy - 6, vw, 12))
    volume_slider.update(mp, volume, dragging_volume)
    volume_slider.draw(surf)


def play_track(track_id, from_pos=0.0):
    global current_index, is_playing, progress, progress_max, progress_timer
    track = next((t for t in music_library if t["id"] == track_id), None)
    if not track:
        return
    current_index = track_id
    is_playing = True
    progress = from_pos
    try:
        m, s = map(int, track.get("duration", "0:00").split(":"))
        progress_max = m * 60 + s
    except Exception:
        progress_max = 180.0
    progress_timer = pygame.time.get_ticks()
    if track.get("file"):
        try:
            mixer.music.load(track["file"])
            try:
                mixer.music.play()
                if from_pos and from_pos > 0:
                    mixer.music.set_pos(from_pos)
            except (pygame.error, Exception) as e:
                print("Warning: seeking not supported by backend; starting from 0. Fallback used.", e)
                mixer.music.play()
        except (pygame.error, FileNotFoundError, Exception) as e:
            print(f"Failed to play {track.get('file')}: {e}")

    if track_id not in play_history:
        play_history.append(track_id)
        save_history()


def toggle_play():
    global is_playing
    if current_index is None:
        if music_library:
            play_track(music_library[0]["id"])
        return
    is_playing = not is_playing
    track = next((t for t in music_library if t["id"] == current_index), None)
    if track and track.get("file"):
        try:
            if is_playing:
                mixer.music.unpause()
            else:
                mixer.music.pause()
        except pygame.error as e:
            print("Playback control error:", e)


def next_track():
    global current_index
    next_in_queue = queue_pop_next()
    if next_in_queue:
        play_track(next_in_queue)
        return

    if current_index is not None and music_library:
        lib = get_library()
        if not lib:
            lib = music_library

        current_track_idx = next((i for i, t in enumerate(lib) if t["id"] == current_index), None)
        if current_track_idx is not None:
            if shuffle_mode:
                next_idx = random.randint(0, len(lib) - 1)
                play_track(lib[next_idx]["id"])
            else:
                if repeat_mode == REPEAT_ONE:
                    play_track(current_index)
                elif repeat_mode == REPEAT_ALL:
                    next_idx = (current_track_idx + 1) % len(lib)
                    play_track(lib[next_idx]["id"])
                else:
                    if current_track_idx + 1 < len(lib):
                        play_track(lib[current_track_idx + 1]["id"])
                    else:
                        is_playing = False
                        mixer.music.stop()


def prev_track():
    global current_index, progress
    if progress > 3.0:
        play_track(current_index, 0.0)
        return

    if current_index is not None and music_library:
        lib = get_library()
        if not lib:
            lib = music_library
        current_track_idx = next((i for i, t in enumerate(lib) if t["id"] == current_index), None)
        if current_track_idx is not None:
            prev_idx = (current_track_idx - 1) % len(lib)
            play_track(lib[prev_idx]["id"])


create_sidebar_ui()

running = True
while running:
    mp = pygame.mouse.get_pos()
    screen.fill(BG)
    draw_sidebar(screen, mp)
    draw_content(screen, mp)
    draw_player(screen, mp)
    draw_playlist_context_menu(screen, mp)
    if confirm_delete["visible"]:
        draw_confirm_delete(screen, mp)
    if show_shortcuts:
        draw_shortcuts(screen)
    if show_create_playlist_popup:
        close_rect, input_rect, create_btn = None, None, None
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        popup_w = 450;
        popup_h = 240
        popup_x = WIDTH // 2 - popup_w // 2;
        popup_y = HEIGHT // 2 - popup_h // 2
        popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
        shadow_rect = popup_rect.copy();
        shadow_rect.x += 4;
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0), shadow_rect, border_radius=16)
        pygame.draw.rect(screen, CARD, popup_rect, border_radius=16)
        title = F_HEAD.render("Create Playlist", True, WHITE)
        screen.blit(title, (popup_x + 30, popup_y + 25))
        close_x = popup_x + popup_w - 50;
        close_y = popup_y + 25
        close_rect = pygame.Rect(close_x, close_y, 32, 32)
        pygame.draw.line(screen, GRAY_L, (close_x + 8, close_y + 8), (close_x + 24, close_y + 24), 2)
        pygame.draw.line(screen, GRAY_L, (close_x + 24, close_y + 8), (close_x + 8, close_y + 24), 2)
        input_y = popup_y + 90
        input_rect = pygame.Rect(popup_x + 30, input_y, popup_w - 60, 50)
        pygame.draw.rect(screen, BTN_H if input_rect.collidepoint(mp) else BTN, input_rect, border_radius=8)
        display_text = new_playlist_name if new_playlist_name else "Playlist name..."
        text_color = WHITE if new_playlist_name else GRAY_D
        text_surf = F_SUB.render(display_text[:30], True, text_color)
        screen.blit(text_surf, (input_rect.x + 16, input_rect.centery - text_surf.get_height() // 2))
        create_btn = pygame.Rect(popup_x + popup_w - 140, popup_y + popup_h - 60, 110, 40)
        pygame.draw.rect(screen, GREEN_H if create_btn.collidepoint(mp) else GREEN, create_btn, border_radius=20)
        create_text = F_BOLD.render("Create", True, WHITE)
        screen.blit(create_text, (create_btn.centerx - create_text.get_width() // 2,
                                  create_btn.centery - create_text.get_height() // 2))
    elif show_playlist_popup:
        popup_w = 400
        popup_h = 60 + len(playlists) * 70 + 140
        popup_x = WIDTH // 2 - popup_w // 2
        popup_y = HEIGHT // 2 - popup_h // 2
        popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
        shadow_rect = popup_rect.copy();
        shadow_rect.x += 4;
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0), shadow_rect, border_radius=16)
        pygame.draw.rect(screen, CARD, popup_rect, border_radius=16)
        title = F_HEAD.render("Add to Playlist", True, WHITE)
        screen.blit(title, (popup_x + 30, popup_y + 25))
        close_x = popup_x + popup_w - 50;
        close_y = popup_y + 25
        close_rect = pygame.Rect(close_x, close_y, 32, 32)
        pygame.draw.line(screen, GRAY_L, (close_x + 8, close_y + 8), (close_x + 24, close_y + 24), 2)
        pygame.draw.line(screen, GRAY_L, (close_x + 24, close_y + 8), (close_x + 8, close_y + 24), 2)
        create_btn_y = popup_y + 80
        create_btn_rect = pygame.Rect(popup_x + 20, create_btn_y, popup_w - 40, 50)
        pygame.draw.rect(screen, BTN_H if create_btn_rect.collidepoint(mp) else BTN, create_btn_rect, border_radius=12)
        pygame.draw.rect(screen, GREEN, create_btn_rect, border_radius=12, width=2)
        plus_x = create_btn_rect.x + 20
        plus_y = create_btn_rect.centery
        pygame.draw.line(screen, GREEN, (plus_x - 6, plus_y), (plus_x + 6, plus_y), 3)
        pygame.draw.line(screen, GREEN, (plus_x, plus_y - 6), (plus_x, plus_y + 6), 3)
        create_text = F_SUB.render("Create New Playlist", True, WHITE)
        screen.blit(create_text, (plus_x + 20, create_btn_rect.centery - create_text.get_height() // 2))
        playlist_popup_buttons = [(create_btn_rect, "CREATE_NEW", close_rect)]
        y = create_btn_y + 70
        for pname in playlists.keys():
            btn_rect = pygame.Rect(popup_x + 20, y, popup_w - 40, 60)
            pygame.draw.rect(screen, BTN_H if btn_rect.collidepoint(mp) else BTN, btn_rect, border_radius=12)
            icon_size = 44
            icon_x = btn_rect.x + 12
            icon_y = btn_rect.centery - icon_size // 2
            icon_rect = pygame.Rect(icon_x, icon_y, icon_size, icon_size)
            for i in range(icon_size):
                ratio = i / icon_size
                color = (int(30 + ratio * 50), int(215 - ratio * 100), int(96 - ratio * 20))
                pygame.draw.rect(screen, color, (icon_x, icon_y + i, icon_size, 1))
            pygame.draw.rect(screen, GREEN, icon_rect, border_radius=6)
            name_text = F_SUB.render(pname, True, WHITE)
            screen.blit(name_text, (icon_x + icon_size + 16, btn_rect.centery - 18))
            count_text = F_SMALL.render(f"{len(playlists[pname])} songs", True, GRAY)
            screen.blit(count_text, (icon_x + icon_size + 16, btn_rect.centery + 4))
            playlist_popup_buttons.append((btn_rect, pname, close_rect))
            y += 70

    if abs(scroll_velocity) > 0.1:
        scroll_offset += scroll_velocity
        scroll_offset = max(0.0, min(max_scroll, scroll_offset))
        scroll_velocity *= 0.92

    if is_playing and current_index is not None and not dragging_progress:
        now = pygame.time.get_ticks()
        elapsed = (now - progress_timer) / 1000.0
        progress = min(progress_max, progress + elapsed)
        progress_timer = now
        if progress >= progress_max - 0.5:
            if repeat_mode == REPEAT_ONE:
                play_track(current_index)
            else:
                next_track()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = e.w, e.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
            create_sidebar_ui()

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if show_shortcuts:
                    show_shortcuts = False
                elif show_create_playlist_popup:
                    show_create_playlist_popup = False
                    new_playlist_name = ""
                elif show_playlist_popup:
                    show_playlist_popup = False
                    popup_track_idx = None
                elif confirm_delete["visible"]:
                    confirm_delete["visible"] = False
                    confirm_delete["playlist"] = None
                elif search_active:
                    search_active = False
                    search_query = ""
                else:
                    running = False
                continue

            if e.key == pygame.K_k:
                show_shortcuts = not show_shortcuts
                continue

            if show_shortcuts:
                continue

            if show_create_playlist_popup:
                if e.key == pygame.K_BACKSPACE:
                    new_playlist_name = new_playlist_name[:-1]
                elif e.key == pygame.K_RETURN:
                    if new_playlist_name.strip():
                        playlists[new_playlist_name.strip()] = []
                        save_playlists()
                        create_sidebar_ui()
                    show_create_playlist_popup = False
                    new_playlist_name = ""
                elif e.unicode and len(new_playlist_name) < 60:
                    new_playlist_name += e.unicode
            elif search_active:
                if e.key == pygame.K_BACKSPACE:
                    search_query = search_query[:-1]
                elif e.key == pygame.K_RETURN:
                    search_active = False
                elif e.unicode and len(search_query) < 120:
                    search_query += e.unicode
                scroll_offset = 0
            else:
                if e.key == pygame.K_SPACE:
                    toggle_play()
                elif e.key == pygame.K_RIGHT:
                    next_track()
                elif e.key == pygame.K_LEFT:
                    prev_track()
                elif e.key == pygame.K_s:
                    shuffle_mode = not shuffle_mode
                elif e.key == pygame.K_r:
                    repeat_mode = (repeat_mode + 1) % 3
                    settings["repeat_mode"] = repeat_mode
                    save_settings()
                elif e.key == pygame.K_m:
                    mini_player_mode = not mini_player_mode
                    settings["mini_player"] = mini_player_mode
                    save_settings()
                elif e.key == pygame.K_SLASH:
                    current_view = "search"
                    search_active = True

        if e.type == pygame.MOUSEWHEEL:
            scroll_velocity -= e.y * 25

        if e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = e.pos

            if show_shortcuts:
                show_shortcuts = False
                continue

            if show_create_playlist_popup:
                if close_rect and close_rect.collidepoint(mx, my):
                    show_create_playlist_popup = False
                    new_playlist_name = ""
                elif create_btn and create_btn.collidepoint(mx, my):
                    if new_playlist_name.strip():
                        playlists[new_playlist_name.strip()] = []
                        save_playlists()
                        create_sidebar_ui()
                    show_create_playlist_popup = False
                    new_playlist_name = ""
                continue

            if show_playlist_popup:
                if close_rect and close_rect.collidepoint(mx, my):
                    show_playlist_popup = False
                    popup_track_idx = None
                else:
                    for btn_rect, pname, _ in playlist_popup_buttons:
                        if btn_rect.collidepoint(mx, my):
                            if pname == "CREATE_NEW":
                                show_playlist_popup = False
                                show_create_playlist_popup = True
                            elif popup_track_idx is not None:
                                add_to_playlist(popup_track_idx, pname)
                                show_playlist_popup = False
                                popup_track_idx = None
                            break
                continue

            if confirm_delete["visible"]:
                if confirm_delete["yes_rect"] and confirm_delete["yes_rect"].collidepoint(mx, my):
                    pname = confirm_delete["playlist"]
                    if pname in playlists:
                        try:
                            del playlists[pname]
                        except Exception:
                            playlists.pop(pname, None)
                        save_playlists()
                        create_sidebar_ui()
                        if selected_playlist == pname:
                            selected_playlist = None
                            current_view = "library"
                    confirm_delete["visible"] = False
                    confirm_delete["playlist"] = None
                elif confirm_delete["no_rect"] and confirm_delete["no_rect"].collidepoint(mx, my):
                    confirm_delete["visible"] = False
                    confirm_delete["playlist"] = None
                else:
                    confirm_delete["visible"] = False
                    confirm_delete["playlist"] = None
                continue

            if playlist_context_menu["visible"]:
                rects = playlist_context_menu.get("rects", {})
                if rects:
                    if rects.get("open") and rects["open"].collidepoint(mx, my):
                        pname = playlist_context_menu["playlist"]
                        if pname in playlists:
                            current_view = "playlist"
                            selected_playlist = pname
                            scroll_offset = 0
                            settings["last_open_playlist"] = selected_playlist
                            save_settings()
                        playlist_context_menu["visible"] = False
                        playlist_context_menu["playlist"] = None
                        playlist_context_menu["rects"] = {}
                        continue
                    elif rects.get("delete") and rects["delete"].collidepoint(mx, my):
                        confirm_delete["visible"] = True
                        confirm_delete["playlist"] = playlist_context_menu["playlist"]
                        playlist_context_menu["visible"] = False
                        playlist_context_menu["playlist"] = None
                        playlist_context_menu["rects"] = {}
                        continue
                    elif rects.get("rect") and not rects["rect"].collidepoint(mx, my):
                        playlist_context_menu["visible"] = False
                        playlist_context_menu["playlist"] = None
                        playlist_context_menu["rects"] = {}
                else:
                    playlist_context_menu["visible"] = False
                    playlist_context_menu["playlist"] = None
                    playlist_context_menu["rects"] = {}

            if e.button == 1:
                for btn in nav_buttons:
                    if btn.handle_click((mx, my)):
                        current_view = btn.view
                        if current_view != "playlist":
                            selected_playlist = None
                        scroll_offset = 0
                for btn in playlist_buttons:
                    if btn.handle_click((mx, my)):
                        current_view = "playlist"
                        selected_playlist = btn.name
                        settings["last_open_playlist"] = selected_playlist
                        save_settings()
                        scroll_offset = 0
                if search_box and search_box.handle_click((mx, my)):
                    search_active = True
                elif search_box:
                    search_active = False

                if control_buttons.get("play"):
                    if control_buttons["play"].rect.collidepoint(mx, my):
                        toggle_play()
                if control_buttons.get("prev") and control_buttons["prev"].handle_click((mx, my)):
                    prev_track()
                if control_buttons.get("next") and control_buttons["next"].handle_click((mx, my)):
                    next_track()
                if control_buttons.get("shuffle") and control_buttons["shuffle"].handle_click((mx, my)):
                    shuffle_mode = not shuffle_mode
                if control_buttons.get("repeat") and control_buttons["repeat"].handle_click((mx, my)):
                    repeat_mode = (repeat_mode + 1) % 3
                    settings["repeat_mode"] = repeat_mode
                    save_settings()

                if progress_slider and progress_slider.handle_click((mx, my)):
                    dragging_progress = True
                    new_progress = progress_max * progress_slider.get_value_at_pos(mx)
                    progress = new_progress
                    progress_timer = pygame.time.get_ticks()
                    track = next((t for t in music_library if t["id"] == current_index), None)
                    if track and track.get("file"):
                        try:
                            mixer.music.set_pos(new_progress)
                        except (pygame.error, Exception) as e:
                            try:
                                mixer.music.play()
                            except Exception:
                                print("Seeking fallback failed:", e)

                if volume_slider and volume_slider.handle_click((mx, my)):
                    dragging_volume = True
                    volume = volume_slider.get_value_at_pos(mx)
                    settings["volume"] = volume
                    mixer.music.set_volume(volume)
                    save_settings()

                if scrollbar_rect and max_scroll > 0:
                    if scrollbar_rect.collidepoint(mx, my):
                        dragging_scrollbar = True
                        scroll_velocity = 0
                    else:
                        list_y = HEADER_H + 20
                        list_cy = list_y + 36
                        list_h = HEIGHT - PLAYER_H - list_y - 10
                        cx = SIDEBAR_W
                        cw = WIDTH - SIDEBAR_W
                        track_rect = pygame.Rect(cx + cw - 20, list_cy, 20, list_h - 36)
                        if track_rect.collidepoint(mx, my):
                            relative_y = (my - list_cy) / (list_h - 36)
                            scroll_offset = relative_y * max_scroll
                            scroll_offset = max(0.0, min(max_scroll, scroll_offset))
                            scroll_velocity = 0

                clicked_track = False
                for track_row in track_rows:
                    if track_row:
                        action = track_row.handle_click((mx, my))
                        if action == "play":
                            play_track(track_row.track_id)
                            clicked_track = True
                            break
                        elif action == "remove_playlist":
                            if selected_playlist:
                                remove_from_playlist(track_row.track_id, selected_playlist)
                            clicked_track = True
                            break
                        elif action == "queue_next":
                            queue_add(track_row.track_id, play_next=True)
                            clicked_track = True
                            break
                if clicked_track:
                    continue

                if current_view == "settings":
                    r_folder = getattr(draw_settings_page, "_folder_rect", None)
                    r_vol = getattr(draw_settings_page, "_vol_rect", None)
                    r_reps = getattr(draw_settings_page, "_repeat_rects", None)
                    r_mini = getattr(draw_settings_page, "_mini_rect", None)
                    if r_reps:
                        for rr, val in r_reps:
                            if rr.collidepoint(mx, my):
                                settings["repeat_mode"] = val
                                repeat_mode = val
                                save_settings()
                    if r_vol and r_vol.collidepoint(mx, my):
                        rel = (mx - r_vol.x) / r_vol.width
                        rel = max(0.0, min(1.0, rel))
                        settings["volume"] = rel
                        volume = rel
                        mixer.music.set_volume(volume)
                        save_settings()
                    if r_mini and r_mini.collidepoint(mx, my):
                        mini_player_mode = not mini_player_mode
                        settings["mini_player"] = mini_player_mode
                        save_settings()
                    if r_folder and r_folder.collidepoint(mx, my):
                        draw_settings_page.editing_folder = True
                        draw_settings_page.folder_input = settings.get("music_folder", "")
                    else:
                        draw_settings_page.editing_folder = False

                if current_view == "queue" and hasattr(draw_queue_page, "rects"):
                    for idx, quad in enumerate(getattr(draw_queue_page, "rects", [])[:]):
                        if len(quad) == 4:
                            rem_rect, p_rect, drag_rect, tid = quad
                            if drag_rect and drag_rect.collidepoint(mx, my):
                                dragging_queue_item = idx
                                drag_start_pos = my
                                drag_offset = 0
                                break
                            if rem_rect and rem_rect.collidepoint(mx, my):
                                queue_remove_at(idx)
                                break
                            if p_rect and p_rect.collidepoint(mx, my):
                                play_track(tid)
                                try:
                                    play_queue.remove(tid)
                                except ValueError:
                                    pass
                                break

            if e.button == 3:
                clicked_on_playlist = False
                for btn in playlist_buttons:
                    if btn.rect.collidepoint(mx, my):
                        playlist_context_menu["visible"] = True
                        playlist_context_menu["playlist"] = btn.name
                        playlist_context_menu["pos"] = (mx, my)
                        playlist_context_menu["rects"] = {}
                        clicked_on_playlist = True
                        break
                if not clicked_on_playlist:
                    playlist_context_menu["visible"] = False
                    playlist_context_menu["playlist"] = None
                    playlist_context_menu["rects"] = {}

        if e.type == pygame.MOUSEBUTTONUP:
            if dragging_queue_item is not None:
                list_y = HEADER_H + 20
                row_height = int(TRACK_H * min(DPI_SCALE, 1.2))
                padding = 8
                total_offset = drag_offset
                move_by = round(total_offset / (row_height + padding))
                new_idx = dragging_queue_item + move_by
                new_idx = max(0, min(len(play_queue) - 1, new_idx))
                if new_idx != dragging_queue_item:
                    queue_move(dragging_queue_item, new_idx)
                dragging_queue_item = None
                drag_start_pos = None
                drag_offset = 0
            dragging_progress = False
            dragging_volume = False
            dragging_scrollbar = False

        if e.type == pygame.MOUSEMOTION:
            if dragging_queue_item is not None and drag_start_pos is not None:
                drag_offset = e.pos[1] - drag_start_pos
            if dragging_progress and progress_slider:
                new_progress = progress_max * progress_slider.get_value_at_pos(e.pos[0])
                progress = new_progress
                progress_timer = pygame.time.get_ticks()
                track = next((t for t in music_library if t["id"] == current_index), None)
                if track and track.get("file"):
                    try:
                        mixer.music.set_pos(new_progress)
                    except (pygame.error, Exception):
                        pass
            if dragging_volume and volume_slider:
                volume = volume_slider.get_value_at_pos(e.pos[0])
                settings["volume"] = volume
                mixer.music.set_volume(volume)
                save_settings()
            if dragging_scrollbar and max_scroll > 0:
                list_y = HEADER_H + 20
                list_cy = list_y + 36
                list_h = HEIGHT - PLAYER_H - list_y - 10
                lib = get_library()
                content_h = len(lib) * TRACK_H
                bar_h = max(50, int(list_h * (list_h / content_h))) if content_h > 0 else max(50, list_h)
                denom = (list_h - 36 - bar_h)
                relative_y = (e.pos[1] - list_cy - bar_h // 2) / denom if denom != 0 else 0
                scroll_offset = relative_y * max_scroll
                scroll_offset = max(0.0, min(max_scroll, scroll_offset))
                scroll_velocity = 0

    if current_view == "settings" and getattr(draw_settings_page, "editing_folder", False):
        pressed = pygame.key.get_pressed()
        for ev in pygame.event.get(pygame.KEYDOWN):
            if ev.key == pygame.K_RETURN:
                newpath = getattr(draw_settings_page, "folder_input", settings.get("music_folder"))
                if newpath and os.path.isdir(newpath):
                    settings["music_folder"] = newpath
                else:
                    try:
                        os.makedirs(newpath, exist_ok=True)
                        settings["music_folder"] = newpath
                    except Exception as e:
                        print("Invalid folder path:", e)
                music_folder = settings.get("music_folder", music_folder)
                music_library = scan_music_folder(music_folder)
                save_settings()
                draw_settings_page.editing_folder = False
            elif ev.key == pygame.K_BACKSPACE:
                draw_settings_page.folder_input = getattr(draw_settings_page, "folder_input",
                                                          settings.get("music_folder", ""))[:-1]
            else:
                if ev.unicode and len(getattr(draw_settings_page, "folder_input", "")) < 260:
                    draw_settings_page.folder_input = getattr(draw_settings_page, "folder_input", "") + ev.unicode

    pygame.display.flip()
    clock.tick(60)

save_settings()
save_playlists()
save_history()
pygame.quit()
sys.exit()