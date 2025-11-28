import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import signClassNames from '../Assets/class_names.json';
import '../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function SignToText() {
  const [isServerConnected, setIsServerConnected] = useState(false);
  const [predictions, setPredictions] = useState([]);
  const [detectedText, setDetectedText] = useState('');
  const [isDetecting, setIsDetecting] = useState(false);
  const [error, setError] = useState(null);
  const [confidence, setConfidence] = useState(0);
  const [lastDetectedSign, setLastDetectedSign] = useState('');
  const [detectionBuffer, setDetectionBuffer] = useState([]);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const detectionIntervalRef = useRef(null);
  const isDetectingRef = useRef(false);

  // Initialize camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          width: 640, 
          height: 480,
          facingMode: 'user'
        }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (err) {
      console.error('Error accessing camera:', err);
      setError('Unable to access camera. Please grant camera permissions.');
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  };

  // Capture frame and convert to base64
  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return null;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to base64
    return canvas.toDataURL('image/jpeg', 0.8);
  };

  // Detect sign language from video frame
  const detectSign = async () => {
    console.log('detectSign called. isDetecting:', isDetectingRef.current, 'videoRef.current:', !!videoRef.current);
    
    if (!isDetectingRef.current || !videoRef.current) {
      console.log('Skipping detection - not ready');
      return;
    }

    console.log('Video readyState:', videoRef.current.readyState);
    
    try {
      // Capture current frame
      const frameData = captureFrame();
      if (!frameData) {
        console.log('No frame data captured');
        return;
      }
      
      console.log('Sending frame to server...');
      
      // Send to Flask API
      const response = await axios.post(`${API_URL}/predict`, {
        image: frameData
      });
      
      console.log('Server response received:', response.data);
      
      if (response.data.success) {
        const { prediction, confidence: conf, top_predictions } = response.data;
        const confidencePercent = Math.round(conf * 100);
        
        console.log('Detection:', prediction, 'Confidence:', confidencePercent + '%');
        
        setConfidence(confidencePercent);
        setPredictions(top_predictions);
        
        // Only process if confidence is above 50%
        if (conf > 0.50) {
          // Add to detection buffer for stabilization
          setDetectionBuffer(prev => {
            const newBuffer = [...prev, prediction].slice(-4); // Keep last 4 detections
            
            // Count occurrences in buffer
            const counts = {};
            newBuffer.forEach(sign => {
              counts[sign] = (counts[sign] || 0) + 1;
            });
            
            // Check if any sign appears at least 2 times in last 4 frames
            const stableSign = Object.keys(counts).find(sign => counts[sign] >= 2);
            
            if (stableSign && stableSign !== lastDetectedSign) {
              console.log('Stable detection found:', stableSign);
              setLastDetectedSign(stableSign);
              setDetectedText(prevText => {
                const newText = prevText ? `${prevText} ${stableSign}` : stableSign;
                console.log('Updated text:', newText);
                return newText;
              });
              
              // Reset after 1.5 seconds
              setTimeout(() => {
                console.log('Resetting last detected sign');
                setLastDetectedSign('');
              }, 1500);
              
              // Clear buffer after successful detection
              return [];
            }
            
            return newBuffer;
          });
        } else {
          console.log('Confidence too low:', confidencePercent + '%');
          // Clear buffer if confidence drops
          setDetectionBuffer([]);
        }
      }
      
    } catch (err) {
      console.error('Error during detection:', err);
      if (err.response) {
        console.error('Server error:', err.response.data);
        setError(`Server error: ${err.response.data.error || 'Unknown error'}`);
      } else if (err.code === 'ERR_NETWORK' || err.code === 'ECONNABORTED') {
        setError('Lost connection to server. Make sure Flask server is still running.');
        setIsServerConnected(false);
        stopDetection();
      } else {
        setError(`Detection error: ${err.message}`);
      }
    }
  };

  // Start detection
  const startDetection = async () => {
    if (!isServerConnected) {
      setError('Server not connected. Please make sure Flask server is running.');
      return;
    }
    
    console.log('Starting detection...');
    setIsDetecting(true);
    isDetectingRef.current = true;
    setError(null);
    setLastDetectedSign('');
    await startCamera();
    
    // Start detection loop (every 300ms for faster response)
    console.log('Setting up detection interval...');
    detectionIntervalRef.current = setInterval(() => {
      console.log('Calling detectSign...');
      detectSign();
    }, 300);
  };

  // Stop detection
  const stopDetection = () => {
    setIsDetecting(false);
    isDetectingRef.current = false;
    if (detectionIntervalRef.current) {
      clearInterval(detectionIntervalRef.current);
    }
    stopCamera();
  };

  // Clear detected text
  const clearText = () => {
    setDetectedText('');
    setPredictions([]);
    setConfidence(0);
  };

  // Check server connection
  useEffect(() => {
    const checkServer = async () => {
      try {
        const response = await axios.get(`${API_URL}/health`, {
          timeout: 3000,
          headers: {
            'Content-Type': 'application/json',
          }
        });
        console.log('Health check response:', response.data);
        if (response.data.status === 'ok') {
          if (response.data.model_loaded) {
            setIsServerConnected(true);
            setError(null);
          } else {
            setIsServerConnected(false);
            setError('Server is running but model is not loaded properly.');
          }
        } else {
          setIsServerConnected(false);
          setError('Server returned unexpected status.');
        }
      } catch (err) {
        console.error('Server connection error:', err);
        if (err.code === 'ECONNABORTED' || err.code === 'ERR_NETWORK') {
          setError('Cannot connect to Flask server. Make sure server is running on http://localhost:5000');
        } else if (err.response) {
          setError(`Server error: ${err.response.status} - ${err.response.statusText}`);
        } else {
          setError('Network error. Check if Flask server is running: python server/app.py');
        }
        setIsServerConnected(false);
      }
    };

    checkServer();
    const interval = setInterval(checkServer, 5000); // Check every 5 seconds

    return () => {
      clearInterval(interval);
      stopCamera();
    };
  }, []);

  return (
    <div className='container-fluid mt-4 px-3 px-md-4'>
      <div className='row'>
        <div className='col-12 text-center mb-4'>
          <h2 className='h3 h2-md'>Sign Language to Text</h2>
          <p className='text-muted small'>Detect sign language gestures in real-time using AI</p>
          <div className='d-flex justify-content-center align-items-center gap-2'>
            <span className={`badge ${isServerConnected ? 'bg-success' : 'bg-danger'}`}>
              <i className={`fa fa-circle me-1`}></i>
              Server {isServerConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className='row mb-3'>
          <div className='col-12'>
            <div className='alert alert-warning' role='alert'>
              <strong>⚠️ {error}</strong>
              {!isServerConnected && (
                <div className='mt-2'>
                  <small>
                    To start the server, run in terminal:<br/>
                    <code className='d-block mt-1 p-2 bg-light text-dark rounded small'>cd server && pip install -r requirements.txt && python app.py</code>
                  </small>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className='row g-3'>
        {/* Video Feed */}
        <div className='col-12 col-lg-6'>
          <div className='card'>
            <div className='card-header'>
              <h5 className='mb-0 h6'>Camera Feed</h5>
            </div>
            <div className='card-body text-center p-2 p-md-3'>
              <video
                ref={videoRef}
                width='100%'
                height='auto'
                style={{ 
                  border: '2px solid #ddd', 
                  borderRadius: '8px',
                  backgroundColor: '#000',
                  maxHeight: '400px',
                  objectFit: 'contain'
                }}
              />
              <canvas ref={canvasRef} style={{ display: 'none' }} />
              
              <div className='mt-3'>
                {!isDetecting ? (
                  <button 
                    className='btn btn-success btn-lg w-100 w-sm-auto'
                    onClick={startDetection}
                    disabled={!isServerConnected}
                  >
                    <i className='fa fa-video-camera me-2'></i>
                    Start Detection
                  </button>
                ) : (
                  <button 
                    className='btn btn-danger btn-lg w-100 w-sm-auto'
                    onClick={stopDetection}
                  >
                    <i className='fa fa-stop me-2'></i>
                    Stop Detection
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Results Panel */}
        <div className='col-12 col-lg-6'>
          <div className='card'>
            <div className='card-header d-flex justify-content-between align-items-center'>
              <h5 className='mb-0 h6'>Detection Results</h5>
              <button 
                className='btn btn-sm btn-outline-secondary'
                onClick={clearText}
              >
                Clear
              </button>
            </div>
            <div className='card-body p-2 p-md-3'>
              {/* Current Prediction */}
              {predictions.length > 0 && (
                <div>
                  <h6 className='small'>Current Sign:</h6>
                  <div className='alert alert-info mb-3'>
                    <h4 className='mb-0 h5'>{predictions[0].class.toUpperCase()}</h4>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className='row mt-4'>
        <div className='col-12'>
          <div className='card'>
            <div className='card-header'>
              <h5 className='mb-0 h6'>Instructions</h5>
            </div>
            <div className='card-body p-3'>
              <ol className='mb-0 ps-3 small'>
                <li>Click "Start Detection" to begin camera feed</li>
                <li>Perform sign language gestures in front of the camera</li>
                <li>The system will detect and display the recognized signs</li>
                <li>Make sure you have good lighting and your hands are clearly visible</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignToText;
