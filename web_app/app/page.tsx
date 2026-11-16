'use client';

import React, { useState, useEffect } from 'react';
import { Navbar, ActiveTabType } from '../components/Navbar';
import { ChatInterface } from '../components/ChatInterface';
import { SmtLabView } from '../components/SmtLabView';
import { PapersView } from '../components/PapersView';
import { SettingsModal } from '../components/SettingsModal';
import { ChatSettings } from '../types/chat';

const DEFAULT_SETTINGS: ChatSettings = {
  apiUrl: process.env.NEXT_PUBLIC_TRUTHGPT_API_URL || '',
  apiKey: '',
  model: 'truthgpt-v2-frontier',
  temperature: 0.2,
  maxTokens: 4096,
  enableSwarm: true,
  enableFormalVerification: true,
  enableStreaming: true
};

export default function TruthGPTFrontendPage() {
  const [activeTab, setActiveTab] = useState<ActiveTabType>('chat');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [settings, setSettings] = useState<ChatSettings>(DEFAULT_SETTINGS);

  // Load user settings from localStorage on client mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('tgpt_frontend_settings');
      if (stored) {
        const parsed = JSON.parse(stored);
        setSettings((prev) => ({ ...prev, ...parsed }));
      }
    } catch (e) {
      console.warn('Failed to load settings from localStorage:', e);
    }
  }, []);

  const handleSaveSettings = (newSettings: ChatSettings) => {
    setSettings(newSettings);
    try {
      localStorage.setItem('tgpt_frontend_settings', JSON.stringify(newSettings));
    } catch (e) {
      console.warn('Failed to save settings to localStorage:', e);
    }
  };

  const handleUpdatePartialSettings = (partial: Partial<ChatSettings>) => {
    setSettings((prev) => {
      const updated = { ...prev, ...partial };
      try {
        localStorage.setItem('tgpt_frontend_settings', JSON.stringify(updated));
      } catch (e) {
        console.warn('Failed to save updated settings:', e);
      }
      return updated;
    });
  };

  const handleResetSettings = () => {
    setSettings(DEFAULT_SETTINGS);
    try {
      localStorage.removeItem('tgpt_frontend_settings');
    } catch (e) {
      console.warn('Failed to clear settings:', e);
    }
  };

  return (
    <div className="min-h-screen bg-[#080914] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onOpenSettings={() => setIsSettingsOpen(true)}
        settings={settings}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col">
        {activeTab === 'chat' && (
          <ChatInterface
            settings={settings}
            onUpdateSettings={handleUpdatePartialSettings}
          />
        )}

        {activeTab === 'smt_lab' && <SmtLabView />}

        {activeTab === 'papers' && <PapersView />}
      </main>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settings}
        onSave={handleSaveSettings}
        onReset={handleResetSettings}
      />
    </div>
  );
}
