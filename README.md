# 🎵 Spotify Free Clone

A fully-featured music player application built with Python and Pygame that mimics Spotify's interface and functionality. Play your local MP3 collection with style!

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## ✨ Features

### 🎼 Core Playback
- **MP3 Support** - Play your entire MP3 library
- **Album Art Display** - Automatic extraction and caching of embedded album artwork
- **Playback Controls** - Play, pause, next, previous with keyboard shortcuts
- **Progress Seeking** - Click or drag the progress bar to jump to any position
- **Volume Control** - Adjustable volume with visual slider

### 📚 Library Management
- **Smart Library Scanning** - Automatically reads ID3 tags (title, artist, duration)
- **Search Functionality** - Real-time search across titles and artists
- **Custom Playlists** - Create, manage, and delete playlists
- **Queue System** - Add songs to play next or queue them for later
- **Playlist Persistence** - Your playlists are saved between sessions

### 🎨 User Interface
- **Spotify-Inspired Design** - Clean, modern dark theme interface
- **Responsive Layout** - Adapts to window resizing and fullscreen mode
- **Smooth Scrolling** - Inertia-based scrolling with velocity
- **Animated Elements** - Playback indicators, hover effects, and button animations
- **Album Art Cache** - LRU cache for fast thumbnail loading

### ⚙️ Advanced Features
- **Shuffle Mode** - Randomize playback order
- **Repeat Modes** - Off, Repeat All, or Repeat One
- **Settings Page** - Configure music folder, volume, and repeat preferences
- **Queue Management** - View and manage your play queue
- **Context Menus** - Right-click playlists for quick actions
- **DPI Awareness** - Proper scaling on high-DPI displays
- **Persistent Settings** - All preferences saved to JSON

### ⌨️ Keyboard Shortcuts
- `Space` - Play/Pause
- `Right Arrow` - Next track
- `Left Arrow` - Previous track
- `Esc` - Close popups/Exit app

## 🚀 Installation

### Prerequisites
```bash
pip install pygame mutagen
```

### Quick Start
1. Clone this repository:
```bash
git clone https://github.com/awesomeaarushmishra-afk/Spotify-Free
cd spotify-free
```

2. Create a `music` folder and add your MP3 files:
```bash
mkdir music
# Copy your MP3 files into the music folder
```

3. Run the application:
```bash
python Spotify\ Free.py
```

## 📁 Project Structure
```
spotify-free/
├── Spotify Free.py          # Main application file
├── music/                   # Your MP3 files go here (auto-created)
├── playlists.json          # Saved playlists (auto-generated)
├── settings.json           # User settings (auto-generated)
└── README.md
```

## 🎯 Usage

### Adding Music
1. Place MP3 files in the `music` folder
2. Restart the app or change the music folder in Settings
3. The app will automatically read ID3 tags and album art

### Creating Playlists
1. Click any track's **"Add"** button
2. Select an existing playlist or create a new one
3. Right-click playlists in the sidebar to delete them

### Using the Queue
1. Hover over any track and click **"Play Next"**
2. View your queue from the sidebar
3. Remove songs or reorder playback from the Queue page

### Customizing Settings
1. Navigate to **Settings** in the sidebar
2. Change music folder location
3. Adjust default volume
4. Set preferred repeat mode

## 🛠️ Technical Details

### Built With
- **Python 3.8+** - Core language
- **Pygame 2.0+** - Graphics and audio engine
- **Mutagen** - MP3 metadata and album art extraction

### Key Features Implementation
- **Album Art Caching** - LRU cache (64 items) with dynamic downscaling
- **Safe Seeking** - Fallback mechanisms for unsupported audio formats
- **Smooth Scrolling** - Physics-based velocity scrolling with dampening
- **Memory Efficient** - Text rendering cache and optimized surface usage
- **Cross-Platform** - Works on Windows, macOS, and Linux

### Performance Optimizations
- Lazy loading of track rows (only visible items rendered)
- Cached text surfaces to reduce font rendering overhead
- Efficient album art downscaling and caching
- Minimal redraws with dirty rect tracking

## 🐛 Known Issues
- Seeking may not work reliably with all MP3 encodings (fallback to start)
- Very large libraries (1000+ songs) may have slight scroll lag
- Album art requires proper ID3v2 APIC frames

## 🤝 Contributing

Contributions are welcome! Here are some ways you can help:
- 🐛 Report bugs and issues
- 💡 Suggest new features
- 🔧 Submit pull requests
- 📖 Improve documentation

### Development Setup
```bash
git clone https://github.com/yourusername/spotify-free.git
cd spotify-free
pip install -r requirements.txt  # If you create one
python Spotify\ Free.py
```

## 📝 Roadmap

- [ ] Equalizer support
- [ ] Crossfade between tracks
- [ ] Last.fm scrobbling
- [ ] Lyrics display
- [ ] Playlist import/export
- [ ] Dark/Light theme toggle
- [ ] Visualizer effects
- [ ] FLAC/OGG support

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by [Spotify](https://spotify.com)'s interface design
- Built with [Pygame](https://www.pygame.org/)
- Metadata handling by [Mutagen](https://mutagen.readthedocs.io/)

## 📧 Contact

Found a bug? Have a suggestion? Open an issue or contact me!

---

**⭐ If you like this project, please give it a star!**

Made with ❤️ and Python
