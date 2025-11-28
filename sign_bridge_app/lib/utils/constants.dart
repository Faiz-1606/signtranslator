import 'package:flutter/material.dart';

class AppConstants {
  // Base URL - Change this to your hosted React app URL
  // For development, use your local server or hosted URL
  static const String baseUrl = 'http://192.168.210.53:3000'; // React app on port 3000

  // For production, use your hosted URL:
  // static const String baseUrl = 'https://your-app.netlify.app';

  static const String homeRoute = '/sign-kit/home';
  static const String convertRoute = '/sign-kit/convert';
  static const String signToTextRoute = '/sign-kit/SignToText';
  static const String learnSignRoute = '/sign-kit/learn-sign';
  static const String videosRoute = '/sign-kit/all-videos';
  static const String createVideoRoute = '/sign-kit/create-video';
  static const String feedbackRoute = '/sign-kit/feedback';

  // App Info
  static const String appName = 'Sign Bridge';
  static const String appVersion = '1.0.0';
  static const String appDescription = 'Sign Language Toolkit - Learn, Convert & Create';
}

class AppColors {
  static const Color primaryColor = Color(0xFF6366F1); // Indigo
  static const Color secondaryColor = Color(0xFF8B5CF6); // Purple
  static const Color accentColor = Color(0xFFEC4899); // Pink

  static const Color backgroundColor = Color(0xFFF9FAFB);
  static const Color cardColor = Colors.white;

  static const Color textPrimary = Color(0xFF1F2937);
  static const Color textSecondary = Color(0xFF6B7280);

  static const Color errorColor = Color(0xFFEF4444);
  static const Color successColor = Color(0xFF10B981);
  static const Color warningColor = Color(0xFFF59E0B);

  // Gradient
  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [primaryColor, secondaryColor, accentColor],
  );
}

class AppStrings {
  static const String loading = 'Loading Sign Bridge...';
  static const String noInternet = 'No Internet Connection';
  static const String noInternetMessage = 'Please check your internet connection and try again.';
  static const String retry = 'Retry';
  static const String error = 'Error';
  static const String errorLoadingPage = 'Failed to load page';
}

