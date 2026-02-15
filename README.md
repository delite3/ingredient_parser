# Barcode Scanner App

A professional React Native mobile application built with Expo that provides real-time barcode and QR code scanning capabilities for iOS and Android devices.

## Features

- Real-time barcode scanning using device camera
- Supports 13+ barcode formats (QR, UPC, EAN13, Code128, and more)
- 2-second scan cooldown to prevent duplicate reads
- Intelligent camera permission handling
- Cross-platform compatibility (iOS and Android)
- Clean, modern user interface with visual scan frame

## Quick Start

### Prerequisites

- **Node.js** v16 or higher ([Download](https://nodejs.org/))
- **Expo Go** mobile app ([iOS](https://apps.apple.com/app/expo-go/id982107779) | [Android](https://play.google.com/store/apps/details?id=host.exp.exponent))

### Installation

```bash
# Install dependencies
npm install

# Start development server
npx expo start
```

### Running on Your Device

1. Ensure your phone and computer are on the same network
2. Open Expo Go on your mobile device
3. Scan the QR code displayed in your terminal
   - **iOS**: Use the native Camera app
   - **Android**: Use the Expo Go app scanner
4. Grant camera permissions when prompted

**Remote Access**: Use `npx expo start --tunnel` if your phone and computer are on different networks.

## Usage

1. Launch the app and grant camera permissions
2. Point your camera at any barcode or QR code
3. The app automatically detects and scans the code
4. View the results (type and data) in the alert dialog
5. Tap "Tap to Scan Again" to scan another code

## Supported Barcode Formats

| Format | Common Use |
|--------|------------|
| **QR Code** | URLs, contact info, WiFi credentials |
| **UPC-A / UPC-E** | Retail product barcodes |
| **EAN-13 / EAN-8** | International product codes |
| **Code 39 / 93 / 128** | Inventory, logistics, shipping |
| **PDF417** | Identification documents, boarding passes |
| **Aztec** | Transportation tickets |
| **Data Matrix** | Electronics marking, logistics |
| **Codabar** | Libraries, blood banks |
| **ITF-14** | Packaging and shipping |

## Project Structure

```
ingredient_parser/
├── App.js                 # Main application component
├── index.js              # Application entry point
├── package.json          # Project dependencies and scripts
├── app.json              # Expo configuration
├── assets/               # Application assets
│   ├── adaptive-icon.png # Android adaptive icon
│   ├── favicon.png       # Web favicon
│   ├── icon.png          # App icon
│   └── splash-icon.png   # Splash screen icon
├── node_modules/         # Dependencies (auto-generated)
└── .expo/                # Expo cache (auto-generated)
```

## Development

### Available Scripts

```bash
npm start              # Start Expo development server
npm run android        # Open on Android emulator
npm run ios            # Open on iOS simulator
npm run web            # Open in web browser
```

### Live Reload

- Changes to source files trigger automatic reload
- Shake your device to open the developer menu
- Press `r` in terminal to manually reload
- Press `j` in terminal to open debugger

### Debugging

```bash
# Open Chrome DevTools debugger
npx expo start
# Then press 'j' in terminal

# View logs in terminal
# console.log() output appears automatically

# Clear cache if needed
npx expo start --clear
```

## Troubleshooting

### Camera Permission Issues

If the camera permission was previously denied:

1. Open device Settings
2. Find **Expo Go** in app list
3. Enable **Camera** permission
4. Restart the app

### Connection Issues

**QR code won't scan:**
```bash
# Ensure devices are on the same network
# Or use tunnel mode for remote access
npx expo start --tunnel
```

**App not loading:**
```bash
# Clear cache and restart
npx expo start --clear
```

### Development Issues

**Module not found errors:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**Port already in use:**
```bash
# Use a different port
npx expo start --port 8082
```

## Building for Production

To create standalone builds for distribution:

```bash
# Install Expo Application Services CLI
npm install -g eas-cli

# Login to Expo account (create at expo.dev)
eas login

# Configure project
eas build:configure

# Build for Android
eas build --platform android

# Build for iOS (requires Apple Developer account)
eas build --platform ios
```

## Technical Stack

- **Framework**: React Native 0.81.5
- **Development Platform**: Expo SDK 54
- **Camera & Scanning**: expo-camera 17.0.10, expo-barcode-scanner 13.0.1
- **UI Components**: React Native core components
- **Safe Area Handling**: react-native-safe-area-context 5.6.2

## System Requirements

| Requirement | Specification |
|------------|---------------|
| **Development** | Windows, macOS, or Linux |
| **Node.js** | v16 or higher |
| **iOS** | iOS 13.0+ |
| **Android** | Android 5.0+ (API 21+) |
| **Network** | Required for development and Expo Go |

## Additional Resources

- [Expo Documentation](https://docs.expo.dev/)
- [React Native Documentation](https://reactnative.dev/)
- [expo-camera API Reference](https://docs.expo.dev/versions/latest/sdk/camera/)
- [Expo Go App](https://expo.dev/client)

## License

Created for educational and development purposes.

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Expo SDK**: ~54.0.33  
**Minimum Node**: v16
