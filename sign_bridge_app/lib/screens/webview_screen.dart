import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:permission_handler/permission_handler.dart';
import 'dart:async';
import '../utils/constants.dart';
import '../widgets/no_internet_widget.dart';
import '../widgets/custom_app_bar.dart';

class WebViewScreen extends StatefulWidget {
  const WebViewScreen({super.key});

  @override
  State<WebViewScreen> createState() => _WebViewScreenState();
}

class _WebViewScreenState extends State<WebViewScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;
  bool _hasInternet = true;
  String _currentUrl = '';
  double _loadingProgress = 0.0;
  late StreamSubscription<ConnectivityResult> _connectivitySubscription;

  @override
  void initState() {
    super.initState();
    _initializeWebView();
    _checkConnectivity();
    _requestPermissions();

    // Listen to connectivity changes
    _connectivitySubscription = Connectivity().onConnectivityChanged.listen((ConnectivityResult result) {
      _updateConnectionStatus(result);
    });
  }

  Future<void> _requestPermissions() async {
    // Request camera and microphone permissions for speech recognition
    final cameraStatus = await Permission.camera.request();
    final microphoneStatus = await Permission.microphone.request();

    if (cameraStatus.isDenied || microphoneStatus.isDenied) {
      debugPrint('Camera or Microphone permission denied');
    }

    if (cameraStatus.isPermanentlyDenied || microphoneStatus.isPermanentlyDenied) {
      // Show dialog to open settings
      if (mounted) {
        _showPermissionDialog();
      }
    }
  }

  void _showPermissionDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Permissions Required'),
        content: const Text(
          'Camera and microphone permissions are required for sign language detection. Please enable them in app settings.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              openAppSettings();
              Navigator.pop(context);
            },
            child: const Text('Open Settings'),
          ),
        ],
      ),
    );
  }

  Future<void> _checkConnectivity() async {
    final connectivityResult = await Connectivity().checkConnectivity();
    _updateConnectionStatus(connectivityResult);
  }

  void _updateConnectionStatus(ConnectivityResult result) {
    setState(() {
      _hasInternet = result != ConnectivityResult.none;
    });

    if (_hasInternet && _isLoading) {
      _controller.reload();
    }
  }

  void _initializeWebView() {
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(Colors.white)
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (int progress) {
            setState(() {
              _loadingProgress = progress / 100;
            });
          },
          onPageStarted: (String url) {
            setState(() {
              _isLoading = true;
              _currentUrl = url;
            });
          },
          onPageFinished: (String url) {
            setState(() {
              _isLoading = false;
              _currentUrl = url;
            });
            // Inject JavaScript to handle camera permissions
            _injectPermissionScript();
          },
          onWebResourceError: (WebResourceError error) {
            debugPrint('WebView Error: ${error.description}');
            setState(() {
              _isLoading = false;
            });
          },
          onNavigationRequest: (NavigationRequest request) {
            // Allow all navigation within the app
            return NavigationDecision.navigate;
          },
        ),
      )
      ..enableZoom(true)
      ..addJavaScriptChannel(
        'CameraPermission',
        onMessageReceived: (JavaScriptMessage message) {
          debugPrint('Camera permission message: ${message.message}');
          if (message.message == 'request') {
            _requestPermissions();
          }
        },
      )
      ..loadRequest(Uri.parse('${AppConstants.baseUrl}${AppConstants.homeRoute}'));

    // Enable DOM storage and other features
    _controller.setUserAgent(
      'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
    );

    // Configure Android-specific WebView settings for camera/microphone
    if (_controller.platform is AndroidWebViewController) {
      AndroidWebViewController.enableDebugging(true);
      (_controller.platform as AndroidWebViewController)
        ..setMediaPlaybackRequiresUserGesture(false);
    }
  }

  void _injectPermissionScript() {
    // Inject JavaScript to log camera API status and help debug
    _controller.runJavaScript('''
      (function() {
        console.log('=== Camera Permission Script Injected ===');
        console.log('navigator.mediaDevices:', !!navigator.mediaDevices);
        console.log('getUserMedia:', !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia));
        
        // Test if camera is accessible
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          console.log('getUserMedia API is available');
          
          // Add permission query if available
          if (navigator.permissions && navigator.permissions.query) {
            navigator.permissions.query({ name: 'camera' })
              .then(permissionStatus => {
                console.log('Camera permission status:', permissionStatus.state);
                permissionStatus.onchange = function() {
                  console.log('Camera permission changed to:', this.state);
                };
              })
              .catch(err => console.log('Permission query error:', err));
          }
        } else {
          console.error('getUserMedia API not available!');
        }
        
        // Store original error handler
        window.addEventListener('error', function(e) {
          if (e.message && e.message.includes('camera')) {
            console.error('Camera error event:', e.message);
          }
        });
        
        console.log('=== End Camera Script ===');
      })();
    ''');
  }

  Future<bool> _onWillPop() async {
    if (await _controller.canGoBack()) {
      _controller.goBack();
      return false;
    }
    return true;
  }

  void _reloadPage() {
    _controller.reload();
  }

  @override
  void dispose() {
    _connectivitySubscription.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: _onWillPop,
      child: Scaffold(
        appBar: CustomAppBar(
          onRefresh: _reloadPage,
          onHome: () {
            _controller.loadRequest(
              Uri.parse('${AppConstants.baseUrl}${AppConstants.homeRoute}'),
            );
          },
        ),
        body: Stack(
          children: [
            if (_hasInternet)
              WebViewWidget(controller: _controller)
            else
              NoInternetWidget(onRetry: _reloadPage),

            // Loading Progress Bar
            if (_isLoading)
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                child: LinearProgressIndicator(
                  value: _loadingProgress,
                  backgroundColor: Colors.grey[200],
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    AppColors.primaryColor,
                  ),
                  minHeight: 3,
                ),
              ),
          ],
        ),

        // Bottom Navigation Bar for quick access
        bottomNavigationBar: _buildBottomNavigationBar(),
      ),
    );
  }

  Widget _buildBottomNavigationBar() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavButton(
                icon: Icons.home,
                label: 'Home',
                onTap: () => _controller.loadRequest(
                  Uri.parse('${AppConstants.baseUrl}${AppConstants.homeRoute}'),
                ),
              ),
              _buildNavButton(
                icon: Icons.swap_horiz,
                label: 'Convert',
                onTap: () => _controller.loadRequest(
                  Uri.parse('${AppConstants.baseUrl}${AppConstants.convertRoute}'),
                ),
              ),
              _buildNavButton(
                icon: Icons.translate,
                label: 'Translate',
                onTap: () => _controller.loadRequest(
                  Uri.parse('${AppConstants.baseUrl}${AppConstants.signToTextRoute}'),
                ),
              ),
              _buildNavButton(
                icon: Icons.school,
                label: 'Learn',
                onTap: () => _controller.loadRequest(
                  Uri.parse('${AppConstants.baseUrl}${AppConstants.learnSignRoute}'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: AppColors.primaryColor, size: 24),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(
                fontSize: 11,
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

