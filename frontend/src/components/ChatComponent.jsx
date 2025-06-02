import React, { useState, useEffect, useRef } from 'react';
import styled, { keyframes, css } from 'styled-components';
import { FiSend, FiUpload, FiDownload, FiZap, FiChevronRight } from 'react-icons/fi';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import FeedbackPanel from './FeedbackPanel';

// Define the API base URL
const API_BASE_URL = 'http://localhost:8000';

// Define image URLs for chat avatars
const USER_IMAGE_URL = `${API_BASE_URL}/static/images/user.png`;
const ROBOT_IMAGE_URL = `${API_BASE_URL}/static/images/robot.png`;

// Keyframe animations
const pulseAnimation = keyframes`
  0% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.05); opacity: 1; }
  100% { transform: scale(1); opacity: 0.8; }
`;

const glowPulse = keyframes`
  0%, 100% { box-shadow: 0 0 5px rgba(255, 108, 44, 0.3); }
  50% { box-shadow: 0 0 20px rgba(255, 108, 44, 0.6); }
`;

const rippleEffect = keyframes`
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.05); opacity: 0.5; }
  100% { transform: scale(0.95); opacity: 0.8; }
`;

const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

const gradientFlow = keyframes`
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
`;

const typing = keyframes`
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
`;

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

// Glass morphism component with dynamic sizing
const GlassMorphism = css`
  background: rgba(16, 42, 67, 0.4);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 20px 80px rgba(0, 0, 0, 0.3);
`;

const neuromorphicDesign = css`
  background: linear-gradient(145deg, rgba(15, 40, 64, 0.6), rgba(12, 32, 52, 0.8));
  box-shadow: 
    8px 8px 16px rgba(0, 0, 0, 0.4),
    -8px -8px 16px rgba(255, 255, 255, 0.03);
`;

const gradientBorder = css`
  position: relative;

  &::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    padding: 1px;
    background: linear-gradient(
      90deg, 
      #FF6C2C, 
      #4A90E2, 
      #FF6C2C
    );
    -webkit-mask: 
      linear-gradient(#fff 0 0) content-box, 
      linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    background-size: 300% 100%;
    animation: ${gradientFlow} 8s linear infinite;
    opacity: 0.5;
  }
`;

// Main container
const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 70vh;
  width: 100%;
  max-width: 800px;
  border-radius: 24px;
  overflow: hidden;
  margin: 0 auto;
  position: relative;
  transition: all 0.3s ease;
  ${GlassMorphism}
  ${gradientBorder}

  @media (max-width: 900px) {
    width: 95%;
    height: 75vh;
  }
  
  @media (max-height: 800px) {
    height: 80vh;
  }
`;

// Interactive background elements
const InteractiveBackground = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
  overflow: hidden;
`;

const BackgroundCircle = styled.div`
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
  background: radial-gradient(circle, rgba(255, 108, 44, 0.5) 0%, rgba(255, 108, 44, 0) 70%);
  animation: ${rippleEffect} 10s infinite ease-in-out;
`;

const TopRightCircle = styled(BackgroundCircle)`
  width: 300px;
  height: 300px;
  top: -150px;
  right: -150px;
`;

const BottomLeftCircle = styled(BackgroundCircle)`
  width: 250px;
  height: 250px;
  bottom: -100px;
  left: -100px;
  background: radial-gradient(circle, rgba(74, 144, 226, 0.5) 0%, rgba(74, 144, 226, 0) 70%);
  animation-delay: -5s;
`;

// Stylish header
const ChatHeader = styled.div`
  background: linear-gradient(90deg, #FF6C2C, #ff8751);
  padding: 20px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  
  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
      45deg,
      rgba(255, 255, 255, 0.05),
      rgba(255, 255, 255, 0.05) 10px,
      rgba(255, 255, 255, 0) 10px,
      rgba(255, 255, 255, 0) 20px
    );
    z-index: -1;
  }
`;

const HeaderTitle = styled.div`
  display: flex;
  align-items: center;
  animation: ${fadeIn} 0.5s ease-out;
`;

const ChatbotIcon = styled.div`
  background: rgba(255, 255, 255, 0.2);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.3);
  position: relative;
  
  &::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 50%;
    padding: 2px;
    background: conic-gradient(
      rgba(255, 255, 255, 0.8),
      rgba(255, 255, 255, 0.3),
      rgba(255, 255, 255, 0.8)
    );
    -webkit-mask: 
      linear-gradient(#fff 0 0) content-box, 
      linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    animation: ${spin} 8s linear infinite;
  }

  img {
    width: 24px;
    height: 24px;
    animation: ${pulseAnimation} 3s infinite ease-in-out;
  }
`;

const HeaderText = styled.div`
  h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 0.5px;
    position: relative;
  }
`;

const BetaTag = styled.span`
  background: #4A90E2;
  color: white;
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  margin-left: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  animation: ${pulseAnimation} 2s infinite;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: inline-flex;
  align-items: center;
  
  svg {
    margin-right: 4px;
  }
`;

// Enhanced message container
const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: rgba(10, 25, 47, 0.3);
  scroll-behavior: smooth;
  position: relative;
  
  /* Custom scrollbar design */
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
    border-radius: 2px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(255, 108, 44, 0.3);
    border-radius: 2px;
    box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.1);
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 108, 44, 0.5);
  }
`;

const messageAppear = keyframes`
  from { 
    opacity: 0; 
    transform: translateY(10px); 
    filter: blur(5px);
  }
  to { 
    opacity: 1; 
    transform: translateY(0);
    filter: blur(0);
  }
`;

const Message = styled.div`
  margin-bottom: 20px;
  display: flex;
  flex-direction: ${props => props.isUser ? 'row-reverse' : 'row'};
  align-items: flex-end;
  animation: ${messageAppear} 0.4s forwards ease-out;
  animation-delay: calc(0.1s * ${props => props.index || 0});
`;

const MessageAvatar = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  margin: ${props => props.isUser ? '0 0 0 12px' : '0 12px 0 0'};
  border: 2px solid ${props => props.isUser ? '#FF6C2C' : '#4A90E2'};
  position: relative;
  ${neuromorphicDesign}
  
  &::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 50%;
    box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.3);
    pointer-events: none;
  }
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
`;

const userMessageGlow = keyframes`
  0%, 100% { box-shadow: 0 0 8px rgba(255, 108, 44, 0.2); }
  50% { box-shadow: 0 0 12px rgba(255, 108, 44, 0.3); }
`;

const botMessageGlow = keyframes`
  0%, 100% { box-shadow: 0 0 8px rgba(74, 144, 226, 0.2); }
  50% { box-shadow: 0 0 12px rgba(74, 144, 226, 0.3); }
`;

// Innovative message bubbles with 3D effect
const MessageContent = styled.div`
  padding: 12px 16px;
  border-radius: 18px;
  max-width: 75%;
  color: ${props => props.isUser ? '#ffffff' : '#F5F8FA'};
  border: 1px solid ${props => props.isUser 
    ? 'rgba(255, 255, 255, 0.1)' 
    : 'rgba(255, 255, 255, 0.05)'};
  position: relative;
  overflow: hidden;
  transform-style: preserve-3d;
  perspective: 800px;
    ${props => props.isUser ? css`
    background: linear-gradient(135deg, #FF6C2C, #ff8751);
    box-shadow: 
      0 4px 12px rgba(255, 108, 44, 0.2),
      0 1px 3px rgba(0, 0, 0, 0.1);
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.1);
    animation: ${userMessageGlow} 3s ease-in-out infinite;
  ` : css`
    background: rgba(16, 42, 67, 0.7);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    animation: ${botMessageGlow} 3s ease-in-out infinite;
    
    &::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 1px;
      background: linear-gradient(90deg, 
        rgba(74, 144, 226, 0) 0%, 
        rgba(74, 144, 226, 0.5) 50%, 
        rgba(74, 144, 226, 0) 100%);
    }
  `}
  
  /* Text styling for better readability */
  font-weight: ${props => props.isUser ? '500' : '400'};
  line-height: 1.5;
  letter-spacing: 0.3px;
  font-size: 15px;
  
  a {
    color: ${props => props.isUser ? '#ffffff' : '#4A90E2'};
    text-decoration: none;
    position: relative;
    font-weight: 500;
    
    &:hover {
      text-decoration: none;
    }
    
    &::after {
      content: '';
      position: absolute;
      width: 100%;
      transform: scaleX(0);
      height: 1px;
      bottom: 0;
      left: 0;
      background-color: ${props => props.isUser ? '#ffffff' : '#4A90E2'};
      transform-origin: bottom right;
      transition: transform 0.3s ease-out;
    }
    
    &:hover::after {
      transform: scaleX(1);
      transform-origin: bottom left;
    }
  }
  
  code {
    background-color: rgba(0, 0, 0, 0.2);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
  }
  
  /* Style markdown content better */
  h3, h4 {
    margin-top: 16px;
    margin-bottom: 8px;
  }
  
  ul, ol {
    padding-left: 20px;
  }
  
  p {
    margin: 8px 0;
  }

  /* Add a nice highlight for key parts of text */
  strong {
    display: inline-block;
    position: relative;
    color: ${props => props.isUser ? '#ffffff' : '#4A90E2'};
    font-weight: 600;
    
    &::after {
      content: '';
      position: absolute;
      width: 100%;
      height: 4px;
      bottom: 0;
      left: 0;
      background-color: ${props => props.isUser ? 'rgba(255, 255, 255, 0.3)' : 'rgba(74, 144, 226, 0.3)'};
      border-radius: 2px;
      z-index: -1;
    }
  }
`;

// Typing indicator animation
const TypingIndicator = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
`;

const TypingDot = styled.span`
  width: 8px;
  height: 8px;
  background-color: #4A90E2;
  border-radius: 50%;
  margin: 0 2px;
  display: inline-block;
  animation: ${typing} 1s infinite;
  animation-delay: ${props => props.delay || '0s'};
`;

// File upload container with 3D effects
const FileUploadContainer = styled.div`
  padding: 15px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(10, 25, 47, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  position: relative;
  
  &::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    height: 4px;
    background: linear-gradient(90deg, 
      rgba(255, 255, 255, 0) 0%, 
      rgba(255, 255, 255, 0.05) 50%, 
      rgba(255, 255, 255, 0) 100%);
  }
`;

// Define a styled component for the Q&A response from Excel files
const QAResponseContainer = styled.div`
  margin-bottom: 20px;
  padding: 15px;
  border-radius: 10px;
  background: rgba(16, 42, 67, 0.5);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

const QAQuestion = styled.div`
  font-weight: 600;
  margin-bottom: 10px;
  color: #4A90E2;
`;

const QAAnswer = styled.div`
  margin-bottom: 10px;
`;

const QASeparator = styled.div`
  height: 1px;
  background: linear-gradient(
    90deg, 
    rgba(255, 255, 255, 0) 0%, 
    rgba(255, 255, 255, 0.1) 50%, 
    rgba(255, 255, 255, 0) 100%
  );
  margin: 15px 0;
`;

// Innovative input container
const InputContainer = styled.div`
  display: flex;
  align-items: center;
  padding: 15px 20px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(10, 25, 47, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  position: relative;
`;

const focusGlow = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(255, 108, 44, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(255, 108, 44, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 108, 44, 0); }
`;

// Stylish input field
const MessageInput = styled.input`
  flex: 1;
  border: none;
  border-radius: 20px;
  padding: 12px 20px;
  background: rgba(16, 42, 67, 0.8);
  outline: none;
  margin-right: 12px;
  color: #F5F8FA;
  font-size: 15px;
  transition: all 0.3s;
  box-shadow: 
    inset 0 1px 3px rgba(0, 0, 0, 0.2),
    0 1px 0 rgba(255, 255, 255, 0.05);
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.3);
    font-style: italic;
  }
  
  &:focus {
    background: rgba(16, 42, 67, 0.95);
    animation: ${focusGlow} 2s infinite;
  }
`;

const buttonHover = keyframes`
  0% { transform: translateY(0); }
  100% { transform: translateY(-3px); }
`;

// 3D buttons with hover effects
const SendButton = styled.button`
  background: linear-gradient(45deg, #FF6C2C, #ff8751);
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 
    0 4px 12px rgba(255, 108, 44, 0.3),
    0 2px 4px rgba(0, 0, 0, 0.2),
    inset 0 -2px 0 rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  transform-style: preserve-3d;
  
  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0));
    z-index: 0;
  }
  
  svg {
    z-index: 1;
    transition: transform 0.2s;
    filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.1));
  }
    &:hover {
    box-shadow: 
      0 6px 18px rgba(255, 108, 44, 0.4),
      0 2px 4px rgba(0, 0, 0, 0.2),
      inset 0 -2px 0 rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
    animation: ${buttonHover} 0.3s forwards, ${glowPulse} 2s ease-in-out infinite;
    
    svg {
      transform: scale(1.1);
    }
  }
  
  &:active {
    transform: translateY(2px);
    box-shadow: 
      0 2px 8px rgba(255, 108, 44, 0.4),
      0 1px 2px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(0, 0, 0, 0.1);
  }
  
  &:disabled {
    background: linear-gradient(45deg, #3a4657, #2a3547);
    cursor: not-allowed;
    box-shadow: none;
    
    &:hover {
      animation: none;
      
      svg {
        transform: none;
      }
    }
  }
`;

const FileInput = styled.input`
  display: none;
`;

// Styled file upload button
const FileUploadButton = styled.label`
  display: inline-flex;
  align-items: center;
  padding: 10px 18px;
  background: linear-gradient(45deg, #4A90E2, #5a9ff2);
  color: white;
  border-radius: 12px;
  cursor: pointer;
  margin-right: 10px;
  border: none;
  transition: all 0.2s;
  box-shadow: 
    0 4px 12px rgba(74, 144, 226, 0.3),
    0 2px 4px rgba(0, 0, 0, 0.2),
    inset 0 -2px 0 rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  font-weight: 500;
  letter-spacing: 0.3px;
  transform-style: preserve-3d;
  
  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0));
    z-index: 0;
  }
  
  svg {
    margin-right: 8px;
    z-index: 1;
    transition: transform 0.2s;
    filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.2));
  }
  
  &:hover {
    box-shadow: 
      0 6px 18px rgba(74, 144, 226, 0.4),
      0 2px 4px rgba(0, 0, 0, 0.2),
      inset 0 -2px 0 rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
    animation: ${buttonHover} 0.3s forwards;
    
    svg {
      transform: rotate(-10deg);
    }
  }
  
  &:active {
    transform: translateY(2px);
    box-shadow: 
      0 2px 8px rgba(74, 144, 226, 0.4),
      0 1px 2px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(0, 0, 0, 0.1);
  }
`;

const UploadText = styled.span`
  z-index: 1;
  white-space: nowrap;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
`;

const shimmerBackground = keyframes`
  0% { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
`;

// Elegant file info display
const SelectedFileInfo = styled.div`
  margin-top: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  color: #F5F8FA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px dashed rgba(74, 144, 226, 0.4);
  background: rgba(16, 42, 67, 0.6);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 0 20px rgba(74, 144, 226, 0.1);
  
  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      90deg, 
      rgba(74, 144, 226, 0) 0%, 
      rgba(74, 144, 226, 0.1) 50%, 
      rgba(74, 144, 226, 0) 100%
    );
    background-size: 200% 100%;
    animation: ${shimmerBackground} 2s infinite linear;
  }

  span {
    max-width: 200px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 500;
    z-index: 1;
    display: flex;
    align-items: center;
    
    &::before {
      content: "";
      width: 8px;
      height: 8px;
      background: #4A90E2;
      border-radius: 50%;
      margin-right: 8px;
      display: inline-block;
      animation: ${pulseAnimation} 2s infinite;
    }
  }
`;

// Process file button with 3D effect
const ProcessFileButton = styled.button`
  background: linear-gradient(45deg, #FF6C2C, #ff8751);
  color: white;
  border: none;
  border-radius: 10px;
  padding: 8px 16px 10px;
  cursor: pointer;
  margin-left: 10px;
  transition: all 0.2s;
  box-shadow: 
    0 4px 12px rgba(255, 108, 44, 0.3),
    0 2px 4px rgba(0, 0, 0, 0.2),
    inset 0 -2px 0 rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  font-weight: 500;
  position: relative;
  overflow: hidden;
  z-index: 1;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
  transform-style: preserve-3d;
  
  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0));
    z-index: -1;
  }
  
  &:hover {
    box-shadow: 
      0 6px 18px rgba(255, 108, 44, 0.4),
      0 2px 4px rgba(0, 0, 0, 0.2),
      inset 0 -2px 0 rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
    animation: ${buttonHover} 0.3s forwards;
  }
  
  &:active {
    transform: translateY(2px);
    box-shadow: 
      0 2px 8px rgba(255, 108, 44, 0.4),
      0 1px 2px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(0, 0, 0, 0.1);
  }
  
  &:disabled {
    background: linear-gradient(45deg, #3a4657, #2a3547);
    cursor: not-allowed;
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.2),
      inset 0 1px 2px rgba(0, 0, 0, 0.1);
    
    &:hover {
      animation: none;
    }
  }
  
  display: flex;
  align-items: center;
  
  svg {
    margin-right: 6px;
  }
`;

const spinnerGlow = keyframes`
  0%, 100% { box-shadow: 0 0 10px rgba(74, 144, 226, 0.5); }
  50% { box-shadow: 0 0 20px rgba(74, 144, 226, 0.8); }
`;

// Advanced loading spinner
const LoadingSpinner = styled.div`
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top: 3px solid #4A90E2;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: ${spin} 1s linear infinite, ${spinnerGlow} 2s ease-in-out infinite;
  margin: 0 auto;
  position: relative;
  
  &::before, &::after {
    content: "";
    position: absolute;
    top: -6px;
    left: -6px;
    right: -6px;
    bottom: -6px;
    border-radius: 50%;
    border: 1px solid rgba(74, 144, 226, 0.1);
    animation: ${spin} 3s linear infinite reverse;
  }
  
  &::after {
    top: -12px;
    left: -12px;
    right: -12px;
    bottom: -12px;
    border: 1px dashed rgba(74, 144, 226, 0.1);
    animation: ${spin} 6s linear infinite;
  }
`;

const downloadButtonAnimation = keyframes`
  0% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
  100% { transform: translateY(0); }
`;

// Stylish download button
const DownloadButton = styled.a`
  display: inline-flex;
  align-items: center;
  padding: 10px 18px;
  background: linear-gradient(45deg, #4A90E2, #5a9ff2);
  color: white;
  border-radius: 12px;
  cursor: pointer;
  text-decoration: none;
  font-size: 14px;
  margin-top: 12px;
  transition: all 0.2s;
  width: fit-content;
  box-shadow: 
    0 4px 12px rgba(74, 144, 226, 0.3),
    0 2px 4px rgba(0, 0, 0, 0.2),
    inset 0 -2px 0 rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  font-weight: 500;
  letter-spacing: 0.3px;
  position: relative;
  overflow: hidden;
  animation: ${downloadButtonAnimation} 3s infinite ease-in-out;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
  transform-style: preserve-3d;
  
  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0));
    z-index: 0;
  }
  
  svg {
    margin-right: 8px;
    z-index: 1;
    transition: transform 0.2s;
    filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.2));
  }
  
  span {
    z-index: 1;
  }
  
  &:hover {
    box-shadow: 
      0 6px 18px rgba(74, 144, 226, 0.4),
      0 2px 4px rgba(0, 0, 0, 0.2),
      inset 0 -2px 0 rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
    
    svg {
      transform: translateY(2px);
    }
  }
  
  &:active {
    transform: translateY(2px);
    box-shadow: 
      0 2px 8px rgba(74, 144, 226, 0.4),
      0 1px 2px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(0, 0, 0, 0.1);
  }
`;

// Add a styled component for the feedback toggle button
const FeedbackToggle = styled.button`
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
  cursor: pointer;
  margin-top: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  
  &:hover {
    color: rgba(255, 255, 255, 0.8);
    background: rgba(255, 255, 255, 0.1);
  }
`;

// Modern component implementation
const ChatComponent = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const messagesEndRef = useRef(null);
  const [feedbackVisibility, setFeedbackVisibility] = useState({});  // Track which messages have feedback panel open

  useEffect(() => {
    // Initial welcome message
    setMessages([{
      text: "Hello, I'm Triskell Chatbot 👋, your AI-powered assistant.\n\n" +
            "You can ask me questions or upload an Excel file for analysis.",
      isUser: false,
    }]);
  }, []);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const uploadFile = async () => {
    if (!selectedFile) return;
    
    setIsProcessing(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      setMessages(prev => [...prev, {
        text: `Uploading and processing ${selectedFile.name}...`,
        isUser: true
      }]);
      
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.status === 'success') {
        // Add a success message
        setMessages(prev => [...prev, {
          id: `file-${Date.now()}`,
          text: `File processed successfully! Here are the responses to your questions:`,
          isUser: false
        }]);
        
        // Add each question-answer pair as a separate component with feedback option
        const qaMessage = {
          id: `qa-${Date.now()}`,
          isUser: false,
          isQAContainer: true,  // Special flag for QA containers
          qaItems: response.data.responses.map((item, index) => ({
            id: `qa-item-${Date.now()}-${index}`,
            question: item.question,
            answer: item.response,
            source: item.source || "unknown"
          }))
        };
        
        setMessages(prev => [...prev, qaMessage]);
        
        // Then, add a separate message with just the download button
        setMessages(prev => [...prev, {
          text: "",
          isUser: false,
          showDownload: true,
          downloadOnly: true
        }]);
      } else {
        setMessages(prev => [...prev, {
          text: response.data.message || 'File processed with some issues.',
          isUser: false
        }]);
      }
      
      setSelectedFile(null);
    } catch (error) {
      console.error('Error uploading file:', error);
      setMessages(prev => [...prev, {
        text: 'Error processing the file. Please try again.',
        isUser: false
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Add feedback handler function
  const handleFeedbackSubmit = async (feedbackData) => {
    try {
      // First, try to find the message in the main messages array (for regular chat)
      let message = messages.find(msg => msg.id === feedbackData.messageId);
      let originalQuery = "";
      let originalAnswer = "";
      
      // If not found in main messages, check QA items from Excel files
      if (!message) {
        // Look through all QA containers and their items
        for (const msg of messages) {
          if (msg.isQAContainer && msg.qaItems) {
            // Find the QA item with the matching ID
            const qaItem = msg.qaItems.find(item => item.id === feedbackData.messageId);
            if (qaItem) {
              // Found the QA item! Use its data
              originalQuery = qaItem.question;
              originalAnswer = qaItem.answer;
              break;
            }
          }
        }
      } else {
        // For regular messages, use the message data
        originalQuery = message.question || message.text || "";
        originalAnswer = message.text || "";
      }
      
      // If we couldn't find any data, exit
      if (!originalQuery && !originalAnswer && !message) {
        console.error("Could not find message or QA item for feedback", feedbackData.messageId);
        alert("Error processing feedback. Please try again.");
        return;
      }
      
      // Add the original query and response data
      const completeData = {
        ...feedbackData,
        original_query: originalQuery,
        original_answer: originalAnswer,
        context_used: message?.context || []
      };
      
      console.log("Sending feedback data:", completeData);
      
      // Submit feedback to the backend
      const response = await axios.post(`${API_BASE_URL}/feedback`, completeData);
      
      if (response.data.status === 'success') {
        // Show a success message
        alert("Thank you for your feedback!");
        
        // Close the feedback panel
        setFeedbackVisibility(prev => ({
          ...prev,
          [feedbackData.messageId]: false
        }));
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      alert("Failed to submit feedback. Please try again.");
    }
  };
  
  // Toggle feedback panel visibility for a specific message
  const toggleFeedback = (messageId) => {
    setFeedbackVisibility(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  // Handle canceling feedback
  const handleCancelFeedback = (messageId) => {
    setFeedbackVisibility(prev => ({
      ...prev,
      [messageId]: false
    }));
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = input.trim();
    setMessages(prev => [...prev, { text: userMessage, isUser: true }]);
    setInput('');
    setIsProcessing(true);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, { message: userMessage });
      
      // Add unique ID to each message for feedback reference
      const messageId = Date.now().toString();
      
      setMessages(prev => [...prev, {
        id: messageId,
        text: response.data.response || 'I couldn\'t process that request.',
        isUser: false,
        question: userMessage,  // Store the question for feedback context
        context: response.data.context || []  // Store context chunks if available
      }]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        text: 'Sorry, there was an error processing your request.',
        isUser: false
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <ChatContainer>
      <InteractiveBackground>
        <TopRightCircle />
        <BottomLeftCircle />
      </InteractiveBackground>
      
      <ChatHeader>
        <HeaderTitle>
          <ChatbotIcon>
            <img src={ROBOT_IMAGE_URL} alt="AI Assistant" width="24" height="24" />
          </ChatbotIcon>
          <HeaderText>
            <h2>Triskell Assistant <BetaTag><FiZap size={10} /> BETA</BetaTag></h2>
          </HeaderText>
        </HeaderTitle>
      </ChatHeader>
      
      <MessagesContainer>
        {messages.map((msg, index) => (
          <React.Fragment key={index}>
            {msg.isQAContainer ? (
              // Special rendering for QA items from Excel files
              <div>
                <Message isUser={false} index={index}>
                  <MessageAvatar isUser={false}>
                    <img src={ROBOT_IMAGE_URL} alt="AI Assistant" />
                  </MessageAvatar>
                  <div style={{width: '100%'}}>
                    {msg.qaItems.map((item, qaIndex) => (
                      <QAResponseContainer key={`qa-${qaIndex}`}>
                        <QAQuestion>Question: {item.question}</QAQuestion>
                        <QAAnswer>Answer: {item.answer}</QAAnswer>
                        
                        {/* Feedback toggle for each individual QA item */}
                        <FeedbackToggle onClick={() => toggleFeedback(item.id)}>
                          {feedbackVisibility[item.id] ? 'Hide suggestion form' : 'Suggest a better answer'}
                        </FeedbackToggle>
                        
                        {feedbackVisibility[item.id] && (
                          <FeedbackPanel
                            messageId={item.id}
                            originalAnswer={item.answer}
                            onFeedbackSubmit={handleFeedbackSubmit}
                            onCancel={() => handleCancelFeedback(item.id)}
                          />
                        )}
                        
                        {qaIndex < msg.qaItems.length - 1 && <QASeparator />}
                      </QAResponseContainer>
                    ))}
                  </div>
                </Message>
              </div>
            ) : (
              // Regular message rendering
              <Message isUser={msg.isUser} index={index}>
                <MessageAvatar isUser={msg.isUser}>
                  <img 
                    src={msg.isUser ? USER_IMAGE_URL : ROBOT_IMAGE_URL} 
                    alt={msg.isUser ? "User" : "AI Assistant"} 
                  />
                </MessageAvatar>
                <div style={{width: '100%'}}>
                  <MessageContent isUser={msg.isUser}>
                    {msg.downloadOnly ? (
                      <DownloadButton 
                        href={`${API_BASE_URL}/download-responses`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <FiDownload /> <span>Download All Responses</span>
                      </DownloadButton>
                    ) : (
                      <ReactMarkdown>
                        {msg.text}
                      </ReactMarkdown>
                    )}
                  </MessageContent>
                  
                  {/* For regular messages, add direct feedback button that opens the feedback panel immediately */}
                  {!msg.isUser && !msg.downloadOnly && msg.id && (
                    <>
                      <FeedbackToggle onClick={() => setFeedbackVisibility(prev => ({...prev, [msg.id]: true}))}>
                        Suggest a better answer
                      </FeedbackToggle>
                      
                      {feedbackVisibility[msg.id] && (
                        <FeedbackPanel
                          messageId={msg.id}
                          originalAnswer={msg.text}
                          onFeedbackSubmit={handleFeedbackSubmit}
                          onCancel={() => handleCancelFeedback(msg.id)}
                        />
                      )}
                    </>
                  )}
                </div>
              </Message>
            )}
          </React.Fragment>
        ))}
        <div ref={messagesEndRef} />
        {isProcessing && !selectedFile && (
          <Message isUser={false}>
            <MessageAvatar isUser={false}>
              <img src={ROBOT_IMAGE_URL} alt="AI Assistant" />
            </MessageAvatar>
            <MessageContent isUser={false}>
              <TypingIndicator>
                <TypingDot delay="0s" />
                <TypingDot delay="0.2s" />
                <TypingDot delay="0.4s" />
              </TypingIndicator>
            </MessageContent>
          </Message>
        )}
      </MessagesContainer>
      
      <FileUploadContainer>
        <FileInput 
          type="file" 
          id="file-upload" 
          accept=".xlsx,.xls,.csv"
          onChange={handleFileChange}
        />
        <FileUploadButton htmlFor="file-upload">
          <FiUpload />
          <UploadText>Upload Excel File</UploadText>
        </FileUploadButton>
        
        {selectedFile && (
          <SelectedFileInfo>
            <span>{selectedFile.name}</span>
            <ProcessFileButton 
              onClick={uploadFile}
              disabled={isProcessing}
            >
              {isProcessing ? <><LoadingSpinner style={{width: '14px', height: '14px', margin: '0 6px 0 0'}} /> Processing...</> : <><FiChevronRight /> Process File</>}
            </ProcessFileButton>
          </SelectedFileInfo>
        )}
      </FileUploadContainer>
      
      <InputContainer>
        <MessageInput
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && !isProcessing && sendMessage()}
          placeholder="Ask a question about your data..."
          disabled={isProcessing}
        />
        <SendButton onClick={sendMessage} disabled={isProcessing || !input.trim()}>
          <FiSend />
        </SendButton>
      </InputContainer>
    </ChatContainer>
  );
};

export default ChatComponent;