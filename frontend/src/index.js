import React from 'react';
import ReactDOM from 'react-dom';
import HelpBoard from './components/HelpBoard';

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('help-board');
    if (container) {
        ReactDOM.render(<HelpBoard />, container);
    } else {
        console.error('Container with ID "help-board" not found');
    }
});
