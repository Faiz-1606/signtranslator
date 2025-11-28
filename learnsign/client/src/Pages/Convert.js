import '../App.css'
import React, { useState, useEffect, useRef } from "react";
import Slider from 'react-input-slider';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'font-awesome/css/font-awesome.min.css';

import xbot from '../Models/xbot/xbot.glb';
import ybot from '../Models/ybot/ybot.glb';
import xbotPic from '../Models/xbot/xbot.png';
import ybotPic from '../Models/ybot/ybot.png';

import * as words from '../Animations/words';
import * as alphabets from '../Animations/alphabets';
import { defaultPose } from '../Animations/defaultPose';

import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";

import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

function Convert() {
  const [text, setText] = useState("");
  const [bot, setBot] = useState(ybot);
  const [speed, setSpeed] = useState(0.1);
  const [pause, setPause] = useState(800);
  const [audioInput, setAudioInput] = useState("");

  const componentRef = useRef({});
  const { current: ref } = componentRef;

  let textFromInput = React.createRef();

  const {
    transcript,
    listening,
    resetTranscript,
  } = useSpeechRecognition();

  useEffect(() => {
    setAudioInput(transcript);
  }, [transcript]);

  useEffect(() => {

    ref.flag = false;
    ref.pending = false;

    ref.animations = [];
    ref.characters = [];

    ref.scene = new THREE.Scene();
    ref.scene.background = new THREE.Color(0xdddddd);

    const spotLight = new THREE.SpotLight(0xffffff, 2);
    spotLight.position.set(0, 5, 5);
    ref.scene.add(spotLight);
    ref.renderer = new THREE.WebGLRenderer({ antialias: true });

    // Get the actual canvas container dimensions
    const canvasContainer = document.getElementById("canvas");
    if (!canvasContainer) return;

    const containerWidth = canvasContainer.clientWidth || 640;
    const containerHeight = window.innerHeight - 70;

    ref.camera = new THREE.PerspectiveCamera(
        30,
        containerWidth / containerHeight,
        0.1,
        1000
    )
    ref.renderer.setSize(containerWidth, containerHeight);

    canvasContainer.innerHTML = "";
    canvasContainer.appendChild(ref.renderer.domElement);

    ref.camera.position.z = 1.6;
    ref.camera.position.y = 1.4;

    let loader = new GLTFLoader();
    loader.load(
      bot,
      (gltf) => {
        gltf.scene.traverse((child) => {
          if ( child.type === 'SkinnedMesh' ) {
            child.frustumCulled = false;
          }
    });
        ref.avatar = gltf.scene;
        ref.scene.add(ref.avatar);
        defaultPose(ref);
        // Initial render
        ref.renderer.render(ref.scene, ref.camera);
      },
      (xhr) => {
        console.log(xhr);
      }
    );

    // Handle window resize
    const handleResize = () => {
      const canvasContainer = document.getElementById("canvas");
      if (canvasContainer && ref.renderer && ref.camera) {
        const containerWidth = canvasContainer.clientWidth || 640;
        const containerHeight = window.innerHeight - 70;
        ref.camera.aspect = containerWidth / containerHeight;
        ref.camera.updateProjectionMatrix();
        ref.renderer.setSize(containerWidth, containerHeight);
        if (ref.scene) {
          ref.renderer.render(ref.scene, ref.camera);
        }
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };

  }, [ref, bot]);

  ref.animate = () => {
    if(ref.animations.length === 0){
        ref.pending = false;
      return ;
    }
    requestAnimationFrame(ref.animate);
    if(ref.animations[0].length){
        if(!ref.flag) {
          if(ref.animations[0][0]==='add-text'){
            setText(text + ref.animations[0][1]);
            ref.animations.shift();
          }
          else{
            for(let i=0;i<ref.animations[0].length;){
              let [boneName, action, axis, limit, sign] = ref.animations[0][i]
              if(sign === "+" && ref.avatar.getObjectByName(boneName)[action][axis] < limit){
                  ref.avatar.getObjectByName(boneName)[action][axis] += speed;
                  ref.avatar.getObjectByName(boneName)[action][axis] = Math.min(ref.avatar.getObjectByName(boneName)[action][axis], limit);
                  i++;
              }
              else if(sign === "-" && ref.avatar.getObjectByName(boneName)[action][axis] > limit){
                  ref.avatar.getObjectByName(boneName)[action][axis] -= speed;
                  ref.avatar.getObjectByName(boneName)[action][axis] = Math.max(ref.avatar.getObjectByName(boneName)[action][axis], limit);
                  i++;
              }
              else{
                  ref.animations[0].splice(i, 1);
              }
            }
          }
        }
    }
    else {
      ref.flag = true;
      setTimeout(() => {
        ref.flag = false
      }, pause);
      ref.animations.shift();
    }
    ref.renderer.render(ref.scene, ref.camera);
  }

  const sign = (inputValue) => {
    var str = inputValue.toUpperCase();
    var strWords = str.split(' ');
    setText('');
    for (let word of strWords) {
      if (words[word]) {
        ref.animations.push(['add-text', word + ' ']);
        words[word](ref);
      } else {
        for (const [index, ch] of word.split('').entries()) {
          if (index === word.length - 1)
            ref.animations.push(['add-text', ch + ' ']);
          else
            ref.animations.push(['add-text', ch]);
          alphabets[ch](ref);
        }
      }
    }
    if(!ref.pending){
      ref.pending = true;
      ref.animate();
    }
  };

  const startListening = () =>{
    SpeechRecognition.startListening({continuous: true});
  }

  const stopListening = () =>{
    SpeechRecognition.stopListening();
  }

  return (
    <div className='container-fluid px-3 px-md-4'>
      <div className='row g-3'>
        {/* Avatar Selection - Order 1 on mobile, Order 3 on desktop */}
        <div className='col-12 col-md-2 order-1 order-md-3'>
          <p className='bot-label'>
            Select Avatar
          </p>
          <div className='d-flex flex-row flex-md-column align-items-center justify-content-center gap-3'>
            <img src={xbotPic} className='bot-image' style={{maxWidth: '150px', width: '45%'}} onClick={()=>{setBot(xbot)}} alt='Avatar 1: XBOT'/>
            <img src={ybotPic} className='bot-image' style={{maxWidth: '150px', width: '45%'}} onClick={()=>{setBot(ybot)}} alt='Avatar 2: YBOT'/>
          </div>
          <p className='label-style'>
            Animation Speed: {Math.round(speed*100)/100}
          </p>
          <Slider
            axis="x"
            xmin={0.05}
            xmax={0.50}
            xstep={0.01}
            x={speed}
            onChange={({ x }) => setSpeed(x)}
            className='w-100'
          />
          <p className='label-style'>
            Pause time: {pause} ms
          </p>
          <Slider
            axis="x"
            xmin={0}
            xmax={2000}
            xstep={100}
            x={pause}
            onChange={({ x }) => setPause(x)}
            className='w-100'
          />
        </div>

        {/* Canvas - Order 2 on mobile and desktop */}
        <div className='col-12 col-md-7 order-2 order-md-2'>
          <div id='canvas'/>
        </div>

        {/* Controls - Order 3 on mobile, Order 1 on desktop */}
        <div className='col-12 col-md-3 order-3 order-md-1'>
          {/* Processed Text - Desktop only */}
          <div className='d-none d-md-block'>
            <label className='label-style'>
              Processed Text
            </label>
            <textarea rows={3} value={text} className='w-100 input-style' readOnly />
          </div>
          
          <label className='label-style'>
            Text Input
          </label>
          <textarea rows={3} ref={textFromInput} placeholder='Text input ...' className='w-100 input-style' />
          <button onClick={() => { sign(textFromInput.current.value); }} className='btn btn-primary w-100 btn-style btn-start'>
            Start Animations
          </button>
        </div>
      </div>
    </div>
  )
}

export default Convert;