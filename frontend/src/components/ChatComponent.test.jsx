import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import ChatComponent from './ChatComponent';

// Mock axios
jest.mock('axios');

describe('ChatComponent', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  test('renders welcome message initially', () => {
    render(<ChatComponent />);
    const welcomeMessage = screen.getByText(/Welcome to Excel AI Assistant/i);
    expect(welcomeMessage).toBeInTheDocument();
  });

  test('displays header with title', () => {
    render(<ChatComponent />);
    const headerTitle = screen.getByText(/Excel AI Assistant/i);
    const betaTag = screen.getByText(/BETA/i);
    expect(headerTitle).toBeInTheDocument();
    expect(betaTag).toBeInTheDocument();
  });

  test('allows entering text in input field', () => {
    render(<ChatComponent />);
    const inputField = screen.getByPlaceholderText(/Ask a question about your data/i);
    
    fireEvent.change(inputField, { target: { value: 'Test question' } });
    expect(inputField.value).toBe('Test question');
  });

  test('sends message when send button is clicked', async () => {
    // Mock axios post response
    axios.post.mockResolvedValueOnce({ data: { response: 'This is a test response' } });
    
    render(<ChatComponent />);
    
    // Enter text and click send
    const inputField = screen.getByPlaceholderText(/Ask a question about your data/i);
    fireEvent.change(inputField, { target: { value: 'Test question' } });
    
    const sendButton = screen.getByRole('button', { name: '' }); // The send button has no text
    fireEvent.click(sendButton);
    
    // Verify user message appears
    expect(screen.getByText('Test question')).toBeInTheDocument();
    
    // Wait for the response to appear
    await waitFor(() => {
      expect(screen.getByText('This is a test response')).toBeInTheDocument();
    });
    
    // Check that axios.post was called correctly
    expect(axios.post).toHaveBeenCalledWith('/chat', { message: 'Test question' });
  });

  test('handles file selection', () => {
    render(<ChatComponent />);
    
    // Get the file input (it's hidden but we can still access it for testing)
    const fileInput = document.querySelector('input[type="file"]');
    
    // Create a mock file
    const mockFile = new File(['dummy content'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    
    // Simulate file selection
    fireEvent.change(fileInput, { target: { files: [mockFile] } });
    
    // Check if file name appears
    expect(screen.getByText('test.xlsx')).toBeInTheDocument();
  });
});