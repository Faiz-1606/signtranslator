# Sign Bridge Mobile App

A Flutter mobile application that wraps the Sign Bridge web application using WebView, providing a native mobile experience for iOS and Android.

## 📱 Features

- **Native Mobile Experience**: Smooth WebView integration with native navigation
- **Offline Detection**: Automatic internet connectivity monitoring
- **Camera & Microphone Access**: Full support for speech-to-sign and sign detection features
- **Bottom Navigation**: Quick access to main features (Home, Convert, Learn, Videos)
- **Pull to Refresh**: Easy page reloading
- **Splash Screen**: Beautiful animated splash screen with gradient
- **Back Navigation**: Smart back button handling within WebView
- **Permissions**: Automatic camera and microphone permission requests

## 🚀 Getting Started

### Prerequisites

1. **Flutter SDK**: Install Flutter 3.0 or later
   - Download from: https://flutter.dev/docs/get-started/install
   - Add Flutter to your PATH

2. **Android Studio** (for Android development)
   - Download from: https://developer.android.com/studio
   - Install Android SDK and emulator

3. **Xcode** (for iOS development - Mac only)
   - Download from Mac App Store
   - Install iOS Simulator

4. **Sign Bridge Web App**: Your React app must be running or hosted
   - For local development: Run `npm start` in the `learnsign/client` directory
   - For production: Deploy to Netlify, Vercel, or Firebase Hosting

### Installation

1. **Navigate to the app directory**:
   ```powershell
   cd C:\Users\faizz\Desktop\signtranslator-master\sign_bridge_app
   ```

2. **Install Flutter dependencies**:
   ```powershell
   flutter pub get
   ```

3. **Configure the base URL**:
   
   Open `lib/utils/constants.dart` and update the base URL:
   
   ```dart
   // For local development
   static const String baseUrl = 'http://localhost:3000';
   
   // For production (after deploying your React app)
   static const String baseUrl = 'https://your-app.netlify.app';
   ```

### Running the App

#### On Android Emulator/Device

1. **Start Android emulator** or connect a physical device

2. **Run the app**:
   ```powershell
   flutter run
   ```

3. **For release build**:
   ```powershell
   flutter build apk --release
   ```
   The APK will be in: `build/app/outputs/flutter-apk/app-release.apk`

#### On iOS Simulator/Device (Mac only)

1. **Open iOS Simulator**

2. **Run the app**:
   ```bash
   flutter run
   ```

3. **For release build**:
   ```bash
   flutter build ios --release
   ```

### Testing with Local Development Server

1. **Start your React development server**:
   ```powershell
   cd C:\Users\faizz\Desktop\signtranslator-master\learnsign\client
   npm start
   ```

2. **Find your local IP address**:
   ```powershell
   ipconfig
   ```
   Look for "IPv4 Address" (e.g., 192.168.1.100)

3. **Update the base URL** in `lib/utils/constants.dart`:
   ```dart
   static const String baseUrl = 'http://192.168.1.100:3000';
   ```

4. **Run the Flutter app**:
   ```powershell
   cd C:\Users\faizz\Desktop\signtranslator-master\sign_bridge_app
   flutter run
   ```

## 📦 Building for Production

### Android

1. **Build APK**:
   ```powershell
   flutter build apk --release
   ```

2. **Build App Bundle** (for Play Store):
   ```powershell
   flutter build appbundle --release
   ```

### iOS (Mac only)

1. **Build for iOS**:
   ```bash
   flutter build ios --release
   ```

2. **Archive in Xcode**:
   - Open `ios/Runner.xcworkspace` in Xcode
   - Select Product > Archive
   - Submit to App Store

## 🔧 Configuration

### App Name & Icon

- **App Name**: Edit in `pubspec.yaml` and platform-specific files
- **App Icon**: Replace images in:
  - Android: `android/app/src/main/res/mipmap-*/ic_launcher.png`
  - iOS: `ios/Runner/Assets.xcassets/AppIcon.appiconset/`

### Permissions

Permissions are already configured in:
- **Android**: `android/app/src/main/AndroidManifest.xml`
- **iOS**: `ios/Runner/Info.plist`

### WebView Settings

Customize WebView behavior in `lib/screens/webview_screen.dart`:
- JavaScript mode
- User agent
- Zoom controls
- Navigation handling

## 📂 Project Structure

```
sign_bridge_app/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── screens/
│   │   ├── splash_screen.dart    # Splash screen with animation
│   │   └── webview_screen.dart   # Main WebView screen
│   ├── widgets/
│   │   ├── custom_app_bar.dart   # Custom app bar
│   │   └── no_internet_widget.dart # No internet indicator
│   └── utils/
│       └── constants.dart        # App constants and colors
├── android/                      # Android-specific files
├── ios/                          # iOS-specific files
└── pubspec.yaml                  # Flutter dependencies
```

## 🎨 Customization

### Colors & Theme

Edit `lib/utils/constants.dart`:
```dart
class AppColors {
  static const Color primaryColor = Color(0xFF6366F1);
  static const Color secondaryColor = Color(0xFF8B5CF6);
  // ... more colors
}
```

### Navigation Routes

Add/modify routes in `lib/utils/constants.dart`:
```dart
class AppConstants {
  static const String homeRoute = '/sign-kit/home';
  static const String convertRoute = '/sign-kit/convert';
  // ... more routes
}
```

## 🐛 Troubleshooting

### Common Issues

1. **"Unable to connect to the server"**
   - Ensure your React app is running
   - Check the base URL in `constants.dart`
   - Verify firewall settings

2. **Camera/Microphone not working**
   - Check permissions in device settings
   - Ensure permissions are declared in manifest files
   - For iOS, check Info.plist descriptions

3. **WebView shows blank page**
   - Clear app data and restart
   - Check browser console for JavaScript errors
   - Verify CORS settings on your backend

4. **Build errors**
   - Run `flutter clean`
   - Run `flutter pub get`
   - Update Flutter: `flutter upgrade`

## 📱 Testing

### Run Tests
```powershell
flutter test
```

### Check Flutter Doctor
```powershell
flutter doctor
```

## 🚀 Deployment

### Deploy React App First

Before building the mobile app for production:

1. **Deploy your React app** to a hosting service:
   ```powershell
   cd C:\Users\faizz\Desktop\signtranslator-master\learnsign\client
   npm run build
   # Deploy build folder to Netlify/Vercel/Firebase
   ```

2. **Update base URL** in Flutter app to your production URL

3. **Build mobile app** with production settings

### Hosting Recommendations

- **Netlify**: Easy deployment, automatic HTTPS
- **Vercel**: Great for React apps, automatic deployments
- **Firebase Hosting**: Fast, reliable, good for mobile apps
- **AWS S3 + CloudFront**: Scalable, production-grade

## 📄 License

This project is part of Sign Bridge - Sign Language Toolkit.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Flutter documentation: https://flutter.dev/docs
3. Check WebView plugin docs: https://pub.dev/packages/webview_flutter

## 📝 Notes

- The app requires an active internet connection to load the web content
- Camera and microphone permissions are essential for full functionality
- For iOS, HTTPS is required in production (HTTP only works for localhost)
- Test on real devices for accurate performance evaluation

