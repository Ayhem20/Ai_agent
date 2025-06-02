import React, { useState } from 'react';
import styled from 'styled-components';
import { FiSave } from 'react-icons/fi';

const FeedbackContainer = styled.div`
  margin-top: 10px;
  padding: 15px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const FeedbackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: ${props => props.active ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)'};
  color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
`;

const SuggestionPrompt = styled.p`
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  margin: 0 0 15px 0;
  font-style: italic;
`;

const TextField = styled.textarea`
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.1);
  color: #fff;
  font-family: inherit;
  margin-bottom: 15px;
  resize: vertical;
  min-height: 120px;
`;

const ErrorMessage = styled.p`
  color: #ff6666;
  font-size: 13px;
  margin: -10px 0 15px 0;
  font-style: italic;
`;

const SubmitButton = styled(FeedbackButton)`
  background: rgba(66, 133, 244, 0.3);
  border: 1px solid rgba(66, 133, 244, 0.5);
  opacity: ${props => props.disabled ? 0.5 : 1};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  
  &:hover {
    background: ${props => props.disabled ? 'rgba(66, 133, 244, 0.3)' : 'rgba(66, 133, 244, 0.4)'};
  }
`;

const FeedbackPanel = ({ messageId, originalAnswer, onFeedbackSubmit, onCancel }) => {
  const [editedAnswer, setEditedAnswer] = useState('');
  const [error, setError] = useState('');
  
  const handleSubmit = () => {
    // Validate that the user entered at least one word
    if (!editedAnswer.trim()) {
      setError('Please enter at least one word before submitting.');
      return;
    }
    
    onFeedbackSubmit({
      messageId,
      feedbackType: "correction",
      editedAnswer: editedAnswer,
      ratings: {
        relevance: 5,
        accuracy: 5
      }
    });
    
    // Reset state
    setEditedAnswer('');
    setError('');
  };
  
  return (
    <FeedbackContainer>
      <SuggestionPrompt>
        Thanks for helping me improve! Please provide a better answer that you think would be more helpful:
      </SuggestionPrompt>
      
      <TextField
        placeholder="Enter your suggested answer here..."
        value={editedAnswer}
        onChange={(e) => {
          setEditedAnswer(e.target.value);
          setError(''); // Clear error when user types
        }}
      />
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      
      <div style={{ display: 'flex', gap: '10px' }}>
        <SubmitButton 
          onClick={handleSubmit}
          disabled={!editedAnswer.trim()}
        >
          <FiSave /> Submit Suggestion
        </SubmitButton>
        
        <FeedbackButton onClick={onCancel}>
          Cancel
        </FeedbackButton>
      </div>
    </FeedbackContainer>
  );
};

export default FeedbackPanel;