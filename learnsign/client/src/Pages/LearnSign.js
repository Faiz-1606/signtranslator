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

function LearnSign() {
  const [bot, setBot] = useState(ybot);
  const [speed, setSpeed] = useState(0.1);
  const [pause, setPause] = useState(800);

  const componentRef = useRef({});
  const { current: ref } = componentRef;

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

    ref.camera = new THREE.PerspectiveCamera(
        30,
        window.innerWidth > 768 ? window.innerWidth*0.57 / (window.innerHeight - 70) : window.innerWidth*0.95 / (window.innerHeight - 70),
        0.1,
        1000
    )

    ref.renderer = new THREE.WebGLRenderer({ antialias: true });
    const canvasWidth = window.innerWidth > 768 ? window.innerWidth * 0.57 : window.innerWidth * 0.95;
    ref.renderer.setSize(canvasWidth, (window.innerHeight - 70));
    document.getElementById("canvas").innerHTML = "";
    document.getElementById("canvas").appendChild(ref.renderer.domElement);

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
        const canvasWidth = window.innerWidth > 768 ? window.innerWidth * 0.57 : window.innerWidth * 0.95;
        const canvasHeight = window.innerHeight - 70;
        ref.camera.aspect = canvasWidth / canvasHeight;
        ref.camera.updateProjectionMatrix();
        ref.renderer.setSize(canvasWidth, canvasHeight);
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
    else {
      ref.flag = true;
      setTimeout(() => {
        ref.flag = false
      }, pause);
      ref.animations.shift();
    }
    ref.renderer.render(ref.scene, ref.camera);
  }

  let alphaButtons = [];
  for (let i = 0; i < 26; i++) {
    alphaButtons.push(
        <div className='col-6 col-sm-4 col-md-3' key={`alpha-${i}`}>
            <button className='signs w-100' onClick={()=>{
              if(ref.animations.length === 0){
                alphabets[String.fromCharCode(i + 65)](ref);
              }
            }}>
                {String.fromCharCode(i + 65)}
            </button>
        </div>
    );
  }

  let wordButtons = [];
  for (let i = 0; i < words.wordList.length; i++) {
    wordButtons.push(
        <div className='col-6 col-md-4' key={`word-${i}`}>
            <button className='signs w-100' onClick={()=>{
              if(ref.animations.length === 0){
                words[words.wordList[i]](ref);
              }
            }}>
                {words.wordList[i]}
            </button>
        </div>
    );
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

        {/* Alphabets and Words - Order 3 on mobile, Order 1 on desktop - Mobile uses accordion */}
        <div className='col-12 col-md-3 order-3 order-md-1'>
            {/* Mobile: Accordion view */}
            <div className='d-md-none'>
              <div className="accordion" id="mobileSignsAccordion">
                <div className="accordion-item">
                  <h2 className="accordion-header" id="headingAlphabets">
                    <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseAlphabets" aria-expanded="false" aria-controls="collapseAlphabets">
                      Alphabets
                    </button>
                  </h2>
                  <div id="collapseAlphabets" className="accordion-collapse collapse" aria-labelledby="headingAlphabets" data-bs-parent="#mobileSignsAccordion">
                    <div className="accordion-body p-2">
                      <div className='row g-2'>
                        {alphaButtons}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="accordion-item">
                  <h2 className="accordion-header" id="headingWords">
                    <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseWords" aria-expanded="false" aria-controls="collapseWords">
                      Words
                    </button>
                  </h2>
                  <div id="collapseWords" className="accordion-collapse collapse" aria-labelledby="headingWords" data-bs-parent="#mobileSignsAccordion">
                    <div className="accordion-body p-2">
                      <div className='row g-2'>
                        {wordButtons}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Desktop: Normal view */}
            <div className='d-none d-md-block'>
              <h1 className='heading'>
                Alphabets
              </h1>
              <div className='row g-2'>
                {alphaButtons}
              </div>
              <h1 className='heading'>
                Words
              </h1>
              <div className='row g-2'>
                {wordButtons}
              </div>
            </div>
        </div>
      </div>
    </div>
  )
}

export default LearnSign;
