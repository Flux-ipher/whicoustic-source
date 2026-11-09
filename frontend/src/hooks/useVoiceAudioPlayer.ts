import { useState, useRef, useEffect, useCallback } from 'react';
import { voiceService } from '../services/voiceService';

export interface UseVoiceAudioPlayerReturn {
  playingId: string | null;
  isLoadingAudio: boolean;
  audioError: string | null;
  togglePlayVoice: (voiceId: string, customUrl?: string) => Promise<void>;
  stopAudio: () => void;
}

/**
 * Universal HTML5 audio controller for streaming voice previews,
 * reels, and marketplace models across Whicoustic.
 */
export function useVoiceAudioPlayer(): UseVoiceAudioPlayerReturn {
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [isLoadingAudio, setIsLoadingAudio] = useState<boolean>(false);
  const [audioError, setAudioError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Initialize shared audio instance
  useEffect(() => {
    const audio = new Audio();
    audio.preload = 'none';

    const handleEnded = () => {
      setPlayingId(null);
      setIsLoadingAudio(false);
    };

    const handleWaiting = () => {
      setIsLoadingAudio(true);
    };

    const handlePlaying = () => {
      setIsLoadingAudio(false);
    };

    const handleError = () => {
      setIsLoadingAudio(false);
      setPlayingId(null);
      setAudioError('Failed to load audio stream from voice vault.');
    };

    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('waiting', handleWaiting);
    audio.addEventListener('playing', handlePlaying);
    audio.addEventListener('error', handleError);

    audioRef.current = audio;

    return () => {
      audio.pause();
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('waiting', handleWaiting);
      audio.removeEventListener('playing', handlePlaying);
      audio.removeEventListener('error', handleError);
      audio.src = '';
      audioRef.current = null;
    };
  }, []);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setPlayingId(null);
    setIsLoadingAudio(false);
  }, []);

  const togglePlayVoice = useCallback(
    async (voiceId: string, customUrl?: string) => {
      const audio = audioRef.current;
      if (!audio) return;

      setAudioError(null);

      // If already playing this voice, toggle pause
      if (playingId === voiceId) {
        audio.pause();
        setPlayingId(null);
        setIsLoadingAudio(false);
        return;
      }

      // Switching voices or starting fresh playback
      try {
        setIsLoadingAudio(true);
        audio.pause();

        const streamUrl = customUrl || voiceService.getStreamUrl(voiceId);
        audio.src = streamUrl;
        audio.currentTime = 0;

        await audio.play();
        setPlayingId(voiceId);
      } catch (err: unknown) {
        setIsLoadingAudio(false);
        setPlayingId(null);
        const msg = err instanceof Error ? err.message : 'Audio playback error';
        // Ignore abort errors from rapid user clicking
        if (!msg.toLowerCase().includes('abort')) {
          setAudioError(msg);
        }
      }
    },
    [playingId]
  );

  return {
    playingId,
    isLoadingAudio,
    audioError,
    togglePlayVoice,
    stopAudio,
  };
}
