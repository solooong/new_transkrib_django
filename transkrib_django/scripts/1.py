import os
import sys
import time
import warnings
import torch
import torchaudio
import numpy as np
from sklearn.cluster import KMeans
import librosa
import gc
from collections import defaultdict
import argparse
import subprocess
import tempfile
import json
import datetime
from datetime import datetime

# Отключаем предупреждения
warnings.filterwarnings("ignore")

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Глобальные флаги доступности библиотек
TORCHAUDIO_AVAILABLE = True
SPEECHBRAIN_AVAILABLE = True  
FASTER_WHISPER_AVAILABLE = True

# Принудительная настройка CUDA
def setup_cuda(gpu_id=0):
    """Принудительная настройка CUDA с проверкой доступности"""
    if not torch.cuda.is_available():
        raise RuntimeError("❌ CUDA не доступна! Запуск невозможен.")
    
    if gpu_id >= torch.cuda.device_count():
        available_gpus = torch.cuda.device_count()
        raise RuntimeError(f"❌ GPU {gpu_id} не существует. Доступно GPU: {available_gpus}")
    
    torch.cuda.set_device(gpu_id)
    device = torch.device(f'cuda:{gpu_id}')
    
    print("=== ПРИНУДИТЕЛЬНАЯ НАСТРОЙКА CUDA ===")
    print(f"Доступно GPU: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        memory = torch.cuda.get_device_properties(i).total_memory / 1e9
        print(f"GPU {i}: {torch.cuda.get_device_name(i)} - Память: {memory:.1f} GB")
    
    print(f"Текущий GPU: {gpu_id} ({torch.cuda.get_device_name(gpu_id)})")
    print(f"Используется устройство: {device}")
    
    return device

def check_cuda_memory():
    """Проверяем доступную память GPU"""
    torch.cuda.empty_cache()
    memory_allocated = torch.cuda.memory_allocated() / 1e9
    memory_cached = torch.cuda.memory_reserved() / 1e9
    
    print(f"Используется памяти GPU: {memory_allocated:.2f} GB")
    print(f"Зарезервировано памяти GPU: {memory_cached:.2f} GB")
    
    return memory_allocated, memory_cached

try:
    import torchaudio
    TORCHAUDIO_AVAILABLE = True
except ImportError as e:
    TORCHAUDIO_AVAILABLE = False

if TORCHAUDIO_AVAILABLE:
    try:
        from speechbrain.inference.speaker import EncoderClassifier
        SPEECHBRAIN_AVAILABLE = True
    except Exception as e:
        SPEECHBRAIN_AVAILABLE = False
else:
    SPEECHBRAIN_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

def get_ffmpeg_path():
    """Возвращает путь к ffmpeg, проверяя несколько вариантов"""
    # Сначала проверяем ffmpeg в PATH
    ffmpeg_commands = ['ffmpeg', 'ffmpeg.exe']
    
    for cmd in ffmpeg_commands:
        try:
            result = subprocess.run(
                [cmd, '-version'], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=5
            )
            if result.returncode == 0:
                return cmd
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    # Если не нашли в PATH, ищем в директории скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_in_script_dir = os.path.join(script_dir, 'ffmpeg.exe')
    
    if os.path.exists(ffmpeg_in_script_dir):
        print(f"✅ FFmpeg найден в директории скрипта: {ffmpeg_in_script_dir}")
        # Проверяем, что он работает
        try:
            result = subprocess.run(
                [ffmpeg_in_script_dir, '-version'], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=5
            )
            if result.returncode == 0:
                return ffmpeg_in_script_dir
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    # Также проверяем текущую рабочую директорию
    ffmpeg_in_cwd = os.path.join(os.getcwd(), 'ffmpeg.exe')
    if os.path.exists(ffmpeg_in_cwd):
        print(f"✅ FFmpeg найден в текущей директории: {ffmpeg_in_cwd}")
        try:
            result = subprocess.run(
                [ffmpeg_in_cwd, '-version'], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=5
            )
            if result.returncode == 0:
                return ffmpeg_in_cwd
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    return None

def check_ffmpeg():
    """Проверяем наличие FFmpeg в системе"""
    ffmpeg_path = get_ffmpeg_path()
    return ffmpeg_path is not None

def convert_audio_to_wav(input_path, output_path=None):
    """Конвертирует аудиофайл в WAV формат с помощью FFmpeg"""
    if output_path is None:
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"converted_{os.path.basename(input_path)}.wav")
    
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        raise Exception("FFmpeg не найден. Установите FFmpeg или поместите ffmpeg.exe в директорию со скриптом.")
    
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            ffmpeg_path, '-y', '-i', input_path,
            '-ac', '1', '-ar', '16000', '-acodec', 'pcm_s16le',
            output_path
        ]
        
        print(f"Конвертация {os.path.basename(input_path)} в WAV...")
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        else:
            raise Exception("Конвертация не удалась - выходной файл не создан")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Ошибка конвертации: {e.stderr}")

def trim_audio_file(input_path, start_sec, duration_sec, output_path=None):
    """
    Обрезает аудиофайл с помощью FFmpeg и сразу конвертирует его в формат для Whisper (16kHz, mono, WAV).
    """
    if output_path is None:
        temp_dir = tempfile.gettempdir()
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(temp_dir, f"trimmed_{base_name}_{int(start_sec)}.wav")
    
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        raise Exception("FFmpeg не найден. Поместите ffmpeg.exe в директорию со скриптом или добавьте в PATH.")
    
    # -ss перед -i работает гораздо быстрее (поиск по ключевым кадрам)
    cmd = [ffmpeg_path, '-y', '-ss', str(start_sec), '-i', input_path]
    
    if duration_sec is not None:
        cmd.extend(['-t', str(duration_sec)])
        
    cmd.extend([
        '-ac', '1',
        '-ar', '16000',
        '-acodec', 'pcm_s16le',
        output_path
    ])
    
    duration_str = f"{duration_sec}с" if duration_sec else "до конца файла"
    print(f"✂️ Обрезка аудио: начало={start_sec}с, длительность={duration_str}...")
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"✅ Аудио успешно обрезано и сконвертировано: {output_path}")
            return output_path
        else:
            raise Exception("Обрезка не удалась - выходной файл не создан или пуст")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Ошибка обрезки FFmpeg: {e.stderr}")

def is_supported_format(file_path):
    supported_direct = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
    file_ext = os.path.splitext(file_path.lower())[1]
    return file_ext in supported_direct

def needs_conversion(file_path):
    needs_conv_formats = ['.amr', '.3gp', '.wma', '.aac']
    file_ext = os.path.splitext(file_path.lower())[1]
    return file_ext in needs_conv_formats

def prepare_audio_file(audio_path):
    """Подготавливает аудиофайл для обработки (без обрезки)"""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Файл не найден: {audio_path}")
    
    file_ext = os.path.splitext(audio_path.lower())[1]
    
    if is_supported_format(audio_path):
        return audio_path
    
    if needs_conversion(audio_path):
        if not check_ffmpeg():
            raise Exception("FFmpeg не найден. Для конвертации файлов установите FFmpeg")
        return convert_audio_to_wav(audio_path)
    
    return audio_path

class ECAPADiarizer:
    def __init__(self, device="cuda"):
        if not SPEECHBRAIN_AVAILABLE:
            raise ImportError("SpeechBrain не доступен.")
        if not torch.cuda.is_available():
            raise RuntimeError("❌ CUDA недоступна для диаризации!")
        
        if isinstance(device, str):
            device = torch.device(device)
            
        self.classifier = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            run_opts={"device": str(device), "savedir": "tmp_ecapa"}
        )
        self.device = device

    def diarize(self, audio_path, segments):
        try:
            waveform, sr = librosa.load(audio_path, sr=16000, mono=True)
            waveform = torch.tensor(waveform).unsqueeze(0).to(self.device)
            
            embeddings = []
            valid_segments = []
            
            for segment in segments:
                start_sample = int(segment['start'] * sr)
                end_sample = int(segment['end'] * sr)
                
                if end_sample - start_sample < 200:
                    continue
                
                seg_waveform = waveform[:, start_sample:end_sample]
                if seg_waveform.shape[1] < 200:
                    continue
                
                try:
                    embedding = self.classifier.encode_batch(seg_waveform).squeeze().cpu().numpy()
                    embeddings.append(embedding)
                    valid_segments.append(segment)
                except Exception:
                    continue
            
            if not embeddings:
                for segment in segments:
                    segment['speaker'] = "SPEAKER_01"
                return segments
            
            embeddings_array = np.array(embeddings)
            n_speakers = 1 if len(embeddings_array) < 2 else min(self.estimate_speaker_count(embeddings_array), len(embeddings_array))
            
            if n_speakers > 1:
                kmeans = KMeans(n_clusters=n_speakers, random_state=0, n_init='auto').fit(embeddings_array)
                speaker_labels = kmeans.labels_
            else:
                speaker_labels = [0] * len(valid_segments)
            
            for i, segment in enumerate(valid_segments):
                segment['speaker'] = f"SPEAKER_{speaker_labels[i] + 1:02d}"
            
            for segment in segments:
                if 'speaker' not in segment:
                    segment['speaker'] = "SPEAKER_01"
            
            return segments
        except Exception as e:
            print(f"Diarization error: {str(e)}")
            torch.cuda.empty_cache()
            for segment in segments:
                segment['speaker'] = "SPEAKER_01"
            return segments
    
    def estimate_speaker_count(self, embeddings, max_speakers=5):
        if len(embeddings) <= 1:
            return min(len(embeddings), 1)
        distortions = []
        max_clusters = min(len(embeddings), max_speakers)
        for k in range(1, max_clusters + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=0, n_init='auto').fit(embeddings)
                distortions.append(kmeans.inertia_)
            except:
                continue
        if len(distortions) < 2:
            return 1
        deltas = [distortions[i-1] - distortions[i] for i in range(1, len(distortions))]
        second_derivatives = [deltas[i-1] - deltas[i] for i in range(1, len(deltas))]
        if second_derivatives:
            return min(np.argmax(second_derivatives) + 2, max_speakers)
        return 1

class SpectralDiarizer:
    def __init__(self):
        self.sr = 16000
        
    def diarize(self, audio_path, segments):
        try:
            y, sr = librosa.load(audio_path, sr=self.sr)
            features = []
            valid_segments = []
            
            for segment in segments:
                start_sample = int(segment['start'] * sr)
                end_sample = int(segment['end'] * sr)
                if end_sample - start_sample < 600:
                    continue
                    
                segment_audio = y[start_sample:end_sample]
                mfcc = librosa.feature.mfcc(y=segment_audio, sr=sr, n_mfcc=13)
                spectral_centroid = librosa.feature.spectral_centroid(y=segment_audio, sr=sr)
                spectral_bandwidth = librosa.feature.spectral_bandwidth(y=segment_audio, sr=sr)
                
                feature_vector = np.concatenate([
                    np.mean(mfcc, axis=1),
                    [np.mean(spectral_centroid)],
                    [np.mean(spectral_bandwidth)]
                ])
                features.append(feature_vector)
                valid_segments.append(segment)
            
            if len(features) < 2:
                for segment in segments:
                    segment['speaker'] = "SPEAKER_01"
                return segments
            
            features_array = np.array(features)
            n_speakers = min(2, len(features_array))
            kmeans = KMeans(n_clusters=n_speakers, random_state=0, n_init='auto').fit(features_array)
            
            for i, segment in enumerate(valid_segments):
                segment['speaker'] = f"SPEAKER_{kmeans.labels_[i] + 1:02d}"
            
            for segment in segments:
                if 'speaker' not in segment:
                    segment['speaker'] = "SPEAKER_01"
            return segments
        except Exception as e:
            print(f"Spectral diarization error: {str(e)}")
            for segment in segments:
                segment['speaker'] = "SPEAKER_01"
            return segments

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def format_diarized_text(segments):
    result = []
    for seg in segments:
        start_time = format_time(seg['start'])
        result.append(f"[{start_time}] {seg['speaker']}: {seg['text']}")
    return "\n".join(result)

def transcribe_audio(audio_path, model_size='large-v3-turbo', enable_diarization=True, 
                     diarization_method='spectral', output_path=None, timeout=60000, gpu_id=0,
                     metadata=None, trim_start=0.0, trim_duration=None):
    """Основная функция транскрибации с принудительным использованием CUDA и поддержкой обрезки"""
    
    device = setup_cuda(gpu_id)
    start_time = time.time()
    
    print(f"=== ЗАПУСК ТРАНСКРИПЦИИ НА CUDA (GPU {gpu_id}) ===")
    print(f"Начало транскрибации в {time.strftime('%H:%M:%S')}")
    print(f"Выбранная модель: {model_size}")
    print(f"Разделение спикеров: {'Включено' if enable_diarization else 'Выключено'}")
    if enable_diarization:
        print(f"Метод диаризации: {diarization_method}")
    print(f"Обрабатываемый файл: {os.path.basename(audio_path)}")
    if trim_duration is not None or trim_start > 0:
        print(f"✂️ Режим обрезки: старт={trim_start}с, длительность={trim_duration}с")
    
    check_cuda_memory()
    
    if not FASTER_WHISPER_AVAILABLE:
        raise ImportError("faster-whisper не доступен. Установите: pip install faster-whisper")
    
    # Логика подготовки файла (с обрезкой или без)
    temp_files_to_clean = []
    
    if trim_duration is not None or trim_start > 0:
        # Если нужна обрезка, используем trim_audio_file (он сразу делает и обрезку, и конвертацию в 16kHz mono wav)
        prepared_audio_path = trim_audio_file(audio_path, trim_start, trim_duration)
        temp_files_to_clean.append(prepared_audio_path)
    else:
        # Стандартная подготовка без обрезки
        prepared_audio_path = prepare_audio_file(audio_path)
        if prepared_audio_path != audio_path:
            temp_files_to_clean.append(prepared_audio_path)
    
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    
    if not output_path:
        save_dir = os.path.dirname(audio_path) or "."
        output_path = os.path.join(save_dir, f"{base_name}_transcript.txt")
    
    print(f"Выходной файл будет сохранен как: {output_path}")
    
    output_dir = os.path.dirname(output_path) or "."
    json_info_path = os.path.join(output_dir, f"{base_name}_info.json")
    json_metadata_path = os.path.join(output_dir, f"{base_name}_metadata.json")
    
    try:
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        if metadata:
            with open(json_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print("Загрузка модели Whisper на CUDA...")
        whisper_model = WhisperModel(
            model_size,
            device="cuda",
            compute_type="float16",
            download_root="F:/git/my_git/apps_my/VOXIMA_BOT/bot_DEMO_Voxima_product/whisper_models"
        )
        check_cuda_memory()

        print("Загрузка аудио для транскрибации...")
        audio, _ = librosa.load(prepared_audio_path, sr=16000, mono=True)

        print("Начало транскрибации на CUDA...")
        segments, info = whisper_model.transcribe(
            audio,
            language="ru",
            task="transcribe",
            beam_size=9,
            best_of=120,
            patience=1.0,
            temperature=0,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.5,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=400,
                speech_pad_ms=400  
            )
        )
        
        all_segments = []
        full_text = []
        
        for segment in segments:
            if time.time() - start_time > timeout:
                print(f"⚠️ Превышен общий таймаут {timeout} секунд")
                break
            seg_data = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            }
            all_segments.append(seg_data)
            full_text.append(segment.text.strip())
            print(f"[{format_time(segment.start)} - {format_time(segment.end)}] {segment.text.strip()}")

        outputs = {
            "segments": all_segments,
            "text": " ".join(full_text)
        }

        if enable_diarization and all_segments:
            print(f"Запуск разделения спикеров методом {diarization_method}...")
            try:
                if diarization_method == 'ecapa' and SPEECHBRAIN_AVAILABLE:
                    diarizer = ECAPADiarizer(device)
                else:
                    diarizer = SpectralDiarizer()
                
                diarized_segments = diarizer.diarize(prepared_audio_path, outputs["segments"])
                result_text = format_diarized_text(diarized_segments)
                print(f"✅ Диаризация методом {diarization_method} завершена успешно")
            except Exception as e:
                print(f"❌ Ошибка диаризации: {str(e)}")
                print("🔄 Продолжаем без диаризации...")
                result_text = outputs["text"]
        else:
            result_text = outputs["text"]
            
        print(f"Сохранение результата в: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result_text)
        
        transcription_info = {
            "audio_file": os.path.basename(audio_path),
            "transcript_file": os.path.basename(output_path),
            "model_size": model_size,
            "diarization_enabled": enable_diarization,
            "diarization_method": diarization_method if enable_diarization else "none",
            "gpu_used": gpu_id,
            "transcription_length": len(result_text),
            "segments_count": len(all_segments),
            "processing_time": time.time() - start_time,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata if metadata else {},
            "output_directory": output_dir,
            "trimmed": trim_duration is not None or trim_start > 0,
            "trim_start": trim_start,
            "trim_duration": trim_duration
        }
        
        with open(json_info_path, 'w', encoding='utf-8') as f:
            json.dump(transcription_info, f, ensure_ascii=False, indent=2)
        
        print("=== ТРАНСКРИБАЦИЯ НА CUDA УСПЕШНО ЗАВЕРШЕНА ===")
        print(f"📄 Текст сохранен в: {output_path}")
        print(f"📊 Информация сохранена в: {json_info_path}")
        
        return result_text, transcription_info
            
    finally:
        torch.cuda.empty_cache()
        # Очистка всех временных файлов (и от конвертации, и от обрезки)
        for temp_file in temp_files_to_clean:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"🗑️ Временный файл удален: {temp_file}")
                except Exception:
                    pass

def main():
    parser = argparse.ArgumentParser(description='Whisper Transcriber with Diarization, AMR/M4A support and Trimming')
    parser.add_argument('audio_path', help='Путь к аудиофайлу')
    parser.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3', 'large-v3-turbo'], 
                       default='large-v3-turbo', help='Размер модели Whisper')
    parser.add_argument('--diarize', action='store_true', default=True, help='Разделение по спикерам (по умолчанию вкл)')
    parser.add_argument('--no-diarize', action='store_false', dest='diarize', help='Отключить разделение по спикерам')
    parser.add_argument('--method', choices=['ecapa', 'spectral'], default='spectral', help='Метод диаризации')
    parser.add_argument('--output', help='Путь для сохранения результата')
    parser.add_argument('--timeout', type=int, default=60000, help='Таймаут транскрибации в секундах')
    parser.add_argument('--gpu', type=int, default=1, help='ID GPU для использования')
    parser.add_argument('--metadata', type=str, help='JSON строка с метаданными')
    
    # Аргументы для обрезки
    parser.add_argument('--trim-start', type=float, default=0.0, help='Начало обрезки в секундах (по умолчанию 0)')
    parser.add_argument('--trim-duration', type=float, default=None, help='Длительность обрезки в секундах (по умолчанию до конца файла)')
    parser.add_argument('--trim-end', type=float, default=None, help='Конец обрезки в секундах (альтернатива trim-duration)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.audio_path):
        print(f"❌ Ошибка: файл {args.audio_path} не найден")
        sys.exit(1)
    
    # Логика вычисления длительности обрезки
    trim_duration = args.trim_duration
    if args.trim_end is not None and args.trim_start is not None:
        if args.trim_end <= args.trim_start:
            print("❌ Ошибка: --trim-end должен быть больше --trim-start")
            sys.exit(1)
        trim_duration = args.trim_end - args.trim_start
        print(f"ℹ️ Вычислена длительность обрезки: {trim_duration} сек (на основе --trim-end)")

    if not FASTER_WHISPER_AVAILABLE:
        print("❌ Ошибка: faster-whisper не установлен.")
        sys.exit(1)
    
    if (trim_duration is not None or args.trim_start > 0) and not check_ffmpeg():
        print("❌ Ошибка: FFmpeg не найден. Он необходим для обрезки аудио.")
        sys.exit(1)
    
    if args.diarize and args.method == 'ecapa' and not SPEECHBRAIN_AVAILABLE:
        print("⚠️ Внимание: speechbrain не доступен. Используется спектральный метод.")
        args.method = 'spectral'
    
    metadata = None
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except Exception as e:
            print(f"⚠️ Ошибка парсинга метаданных: {e}")
    
    try:
        result, info = transcribe_audio(
            audio_path=args.audio_path,
            model_size=args.model,
            enable_diarization=args.diarize,
            diarization_method=args.method,
            output_path=args.output,
            timeout=args.timeout,
            gpu_id=args.gpu,
            metadata=metadata,
            trim_start=args.trim_start,
            trim_duration=trim_duration
        )
        print("✅ Транскрибация на CUDA завершена успешно!")
        print(f"\n📊 Сводная информация:")
        print(f"   Файл: {info['audio_file']}")
        print(f"   Модель: {info['model_size']}")
        print(f"   Диаризация: {'Включена' if info['diarization_enabled'] else 'Выключена'}")
        print(f"   Длина текста: {info['transcription_length']} символов")
        print(f"   Время обработки: {info['processing_time']:.2f} секунд")
        if info.get('trimmed'):
            print(f"   ✂️ Обрезка: старт={info['trim_start']}с, длительность={info['trim_duration']}с")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()