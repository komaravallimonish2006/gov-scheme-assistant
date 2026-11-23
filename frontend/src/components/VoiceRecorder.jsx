import React, { useState, useRef } from 'react';
import { Mic, Square, Loader2, AlertCircle } from 'lucide-react';

export default function VoiceRecorder({ onVoiceRecorded, disabled }) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  const startRecording = async () => {
    setErrorMsg('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        // Stop all audio tracks
        stream.getTracks().forEach((track) => track.stop());
        clearInterval(timerRef.current);
        setIsRecording(false);
        setRecordingTime(0);

        if (audioBlob.size > 0) {
          onVoiceRecorded(audioBlob);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          if (prev >= 30) {
            // Auto stop after 30 seconds
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);

    } catch (err) {
      console.error('Mic access error:', err);
      setErrorMsg('Microphone access denied or unavailable.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="flex items-center gap-2">
      {errorMsg && (
        <span className="text-rose-400 text-xs flex items-center gap-1">
          <AlertCircle className="w-3.5 h-3.5" />
          {errorMsg}
        </span>
      )}

      {isRecording ? (
        <button
          type="button"
          onClick={stopRecording}
          className="recording-pulse flex items-center gap-2 px-3 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-medium text-xs shadow-lg transition-all"
          title="Click to stop recording"
        >
          <Square className="w-3.5 h-3.5 fill-current" />
          <span>Stop ({formatTime(recordingTime)})</span>
        </button>
      ) : (
        <button
          type="button"
          onClick={startRecording}
          disabled={disabled}
          className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 text-slate-300 hover:text-amber-400 border border-slate-700 transition-all disabled:opacity-50"
          title="Ask query via Voice (మాట్లాడి అడగండి / बोलकर पूछें)"
        >
          <Mic className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
