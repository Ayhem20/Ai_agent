import { render, screen } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  test('renders Excel AI Agent header', () => {
    render(<App />);
    const headerElement = screen.getByText(/Excel AI Agent/i);
    expect(headerElement).toBeInTheDocument();
  });

  test('renders footer with copyright', () => {
    render(<App />);
    const footerElement = screen.getByText(/Powered by AI - © 2025/i);
    expect(footerElement).toBeInTheDocument();
  });

  test('renders ChatComponent', () => {
    render(<App />);
    // This is a basic structure test
    const mainElement = document.querySelector('main');
    expect(mainElement).toBeInTheDocument();
  });
});
