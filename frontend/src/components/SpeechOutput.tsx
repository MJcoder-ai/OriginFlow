import { useEffect, useRef } from 'react';
import { useAppStore } from '../appStore';

/**
 * Observes AI messages and reads them aloud when voice output is enabled.
 * After speaking, if continuous conversation is enabled, it triggers the
 * voice recorder to listen for the next command.
 */
const SpeechOutput = () => {
  const messages = useAppStore((s) => s.messages);
  const voiceOutputEnabled = useAppStore((s) => s.voiceOutputEnabled);
  const isContinuousConversation = useAppStore((s) => s.isContinuousConversation);
  const startListening = useAppStore((s) => s.startListening);
  const lastSpokenId = useRef<string | null>(null);

  useEffect(() => {
    if (!voiceOutputEnabled) return;
    if (messages.length === 0) return;
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.author !== 'AI') return;
    if (lastSpokenId.current === lastMessage.id) return;

    const synth = (window as any).speechSynthesis;
    if (!synth) return;

    const text = (lastMessage as any).summary || lastMessage.text;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onend = () => {
      if (isContinuousConversation) {
        startListening();
      }
    };
    synth.speak(utterance);
    lastSpokenId.current = lastMessage.id;
  }, [messages, voiceOutputEnabled, isContinuousConversation, startListening]);

  return null;
};

export default SpeechOutput;
