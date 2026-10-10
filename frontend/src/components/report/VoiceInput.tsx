import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Square, RotateCcw, Pencil, CheckCircle, AlertCircle, Waveform, AudioLines } from 'lucide-react';

interface VoiceInputProps {
  transcript: string;
  setTranscript: (v: string) => void;
  onFillFromVoice?: (text: string) => void;
}

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

type RecordingState = 'idle' | 'requesting' | 'recording' | 'error' | 'done';

export const VoiceInput = ({ transcript, setTranscript, onFillFromVoice }: VoiceInputProps) => {
  const [state, setState] = useState<RecordingState>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [waveAmplitudes, setWaveAmplitudes] = useState([0.4, 0.6, 0.8, 0.5, 0.7, 0.4, 0.9, 0.6, 0.5, 0.8]);
  const recognitionRef = useRef<any>(null);
  const waveIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isSupported = typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  const animateWave = () => {
    waveIntervalRef.current = setInterval(() => {
      setWaveAmplitudes(prev => prev.map(() => 0.3 + Math.random() * 0.7));
    }, 150);
  };

  const stopWave = () => {
    if (waveIntervalRef.current) clearInterval(waveIntervalRef.current);
    setWaveAmplitudes(Array(10).fill(0.2));
  };

  const startRecording = async () => {
    if (!isSupported) {
      setState('error');
      setErrorMsg('Voice input is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    setState('requesting');
    setErrorMsg('');

    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setState('error');
      setErrorMsg('Microphone access denied. Please allow microphone permission and try again.');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';

    recognition.onstart = () => {
      setState('recording');
      animateWave();
    };

    let finalTranscript = '';
    recognition.onresult = (event: any) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + ' ';
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      setTranscript((finalTranscript + interim).trim());
    };

    recognition.onerror = (event: any) => {
      stopWave();
      if (event.error === 'not-allowed') {
        setState('error');
        setErrorMsg('Microphone permission was denied.');
      } else if (event.error === 'no-speech') {
        setState('error');
        setErrorMsg('No speech detected. Please try again.');
      } else {
        setState('error');
        setErrorMsg(`Recognition error: ${event.error}. Please try again.`);
      }
    };

    recognition.onend = () => {
      stopWave();
      if (finalTranscript.trim()) {
        setState('done');
      } else if (state === 'recording') {
        setState('idle');
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    stopWave();
    setState('done');
  };

  const resetVoice = () => {
    stopRecording();
    setTranscript('');
    setState('idle');
    setIsEditing(false);
    setErrorMsg('');
  };

  useEffect(() => {
    return () => {
      if (recognitionRef.current) recognitionRef.current.stop();
      stopWave();
    };
  }, []);

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${state === 'recording' ? 'bg-red-500 animate-pulse' : state === 'done' ? 'bg-emerald-500' : 'bg-slate-300'}`} />
          <span className="text-sm font-semibold text-slate-700">
            {state === 'idle' ? 'Voice Description' :
             state === 'requesting' ? 'Requesting mic access...' :
             state === 'recording' ? 'Recording... speak clearly' :
             state === 'done' ? 'Recording complete' :
             'Voice Error'}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          {!isSupported && (
            <span className="text-[10px] bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full border border-amber-200 font-medium">Chrome/Edge only</span>
          )}
          <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full border border-blue-200 font-medium">🎤 Speech-to-Text</span>
        </div>
      </div>

      {/* Waveform area */}
      <div className="px-4 py-4">
        {state === 'recording' && (
          <div className="flex items-end justify-center gap-0.5 h-12 mb-4">
            {waveAmplitudes.map((amp, i) => (
              <div
                key={i}
                className="w-2 rounded-full bg-blue-500 transition-all duration-150"
                style={{ height: `${amp * 100}%`, opacity: 0.6 + amp * 0.4 }}
              />
            ))}
          </div>
        )}

        {/* Error message */}
        {state === 'error' && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg mb-3">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{errorMsg}</p>
          </div>
        )}

        {/* Transcript area */}
        {(state === 'done' || transcript) && (
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-slate-600">Transcript</span>
              <div className="flex gap-1.5">
                <button
                  type="button"
                  onClick={() => setIsEditing(!isEditing)}
                  className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium transition"
                >
                  <Pencil className="w-3 h-3" />
                  {isEditing ? 'Done' : 'Edit'}
                </button>
                {onFillFromVoice && transcript && (
                  <button
                    type="button"
                    onClick={() => onFillFromVoice(transcript)}
                    className="flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-700 font-medium transition"
                  >
                    <CheckCircle className="w-3 h-3" />
                    Use as Description
                  </button>
                )}
              </div>
            </div>
            {isEditing ? (
              <textarea
                value={transcript}
                onChange={e => setTranscript(e.target.value)}
                rows={3}
                className="w-full text-sm text-slate-800 bg-white border border-blue-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
              />
            ) : (
              <div className="text-sm text-slate-700 bg-white border border-slate-200 rounded-lg px-3 py-2 min-h-[60px] leading-relaxed">
                {transcript || <span className="text-slate-400 italic">Nothing recorded yet...</span>}
              </div>
            )}
          </div>
        )}

        {/* Controls */}
        <div className="flex items-center gap-2">
          {state === 'idle' || state === 'error' ? (
            <button
              type="button"
              onClick={startRecording}
              disabled={!isSupported}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              <Mic className="w-4 h-4" />
              Start Recording
            </button>
          ) : state === 'recording' ? (
            <button
              type="button"
              onClick={stopRecording}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg transition shadow-sm animate-pulse"
            >
              <Square className="w-4 h-4" />
              Stop Recording
            </button>
          ) : state === 'done' ? (
            <button
              type="button"
              onClick={startRecording}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition shadow-sm"
            >
              <Mic className="w-4 h-4" />
              Re-record
            </button>
          ) : null}

          {transcript && (
            <button
              type="button"
              onClick={resetVoice}
              className="flex items-center gap-1.5 px-3 py-2 text-slate-500 hover:text-slate-700 text-sm font-medium transition rounded-lg hover:bg-slate-100"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Clear
            </button>
          )}

          <span className="ml-auto text-[10px] text-slate-400">
            Or type description manually below
          </span>
        </div>
      </div>
    </div>
  );
};
