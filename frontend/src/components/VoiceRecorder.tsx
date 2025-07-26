import { useEffect } from 'react';
import { useAppStore } from '../appStore';

/**
 * Hooks into the browser SpeechRecognition API to capture voice input.
 * When `voiceMode` is `listening`, this component starts speech recognition
 * and streams interim transcripts into state. When a final transcript is
 * received it calls `stopListening` which also submits the command.
 *
 * This component renders nothing and should be mounted once at app root.
 */
const VoiceRecorder = () => {
  const voiceMode = useAppStore((s) => s.voiceMode);
  const stopListening = useAppStore((s) => s.stopListening);
  const updateVoiceTranscript = useAppStore((s) => s.updateVoiceTranscript);

  useEffect(() => {
    const SpeechRecognition: any =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('SpeechRecognition API not supported in this browser.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      let interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }
      if (interimTranscript) {
        updateVoiceTranscript(interimTranscript);
      }
      if (finalTranscript) {
        const cleaned = finalTranscript.trim().toLowerCase();
        if (cleaned === 'stop listening' || cleaned === 'stop') {
          stopListening();
          return;
        }
        stopListening(cleaned);
      }
    };

    recognition.onerror = () => {
      if (voiceMode === 'listening') {
        stopListening();
      }
    };

    if (voiceMode === 'listening') {
      try {
        recognition.start();
      } catch {
        // ignore duplicate start errors
      }
    } else {
      recognition.stop();
    }

    return () => {
      recognition.stop();
    };
  }, [voiceMode, stopListening, updateVoiceTranscript]);

  return null;
};

export default VoiceRecorder;
