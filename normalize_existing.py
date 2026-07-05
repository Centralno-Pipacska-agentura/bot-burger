import os
import shutil
import subprocess

ENTRANCE_DIR = "entrance"
BACKUP_DIR = "entrance_backup"

def normalize_file(input_path, output_path):
    print(f"Normalizing {input_path} -> {output_path}")
    # Using ffmpeg's EBU R128 loudnorm filter.
    # I=-23: Target loudness is -23 LUFS (quieter broadcast standard for comfortable headphone usage).
    # TP=-1.5: Target true peak is -1.5 dBTP to prevent clipping.
    # LRA=11: Loudness range target.
    command = [
        "ffmpeg",
        "-i", input_path,
        "-filter:a", "loudnorm=I=-23:TP=-1.5:LRA=11",
        "-y",
        output_path
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to normalize {input_path}: {e.stderr.decode('utf-8', errors='ignore')}")
        return False

def main():
    if not os.path.exists(ENTRANCE_DIR):
        print(f"Directory {ENTRANCE_DIR} does not exist.")
        return

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"Created backup directory: {BACKUP_DIR}")

    files = [f for f in os.listdir(ENTRANCE_DIR) if os.path.isfile(os.path.join(ENTRANCE_DIR, f))]
    
    success_count = 0
    for file_name in files:
        # Avoid backing up non-audio or hidden files if any, but process all existing mp3s/wavs
        if not file_name.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.aac')):
            continue
            
        src_path = os.path.join(ENTRANCE_DIR, file_name)
        backup_path = os.path.join(BACKUP_DIR, file_name)
        
        # Copy to backup first, ONLY if backup doesn't already exist to preserve the original unmodified audio!
        if not os.path.exists(backup_path):
            print(f"Backing up {file_name} to {BACKUP_DIR}")
            shutil.copy2(src_path, backup_path)
        else:
            print(f"Using existing backup for {file_name}")
        
        # Normalize from backup back to original location
        if normalize_file(backup_path, src_path):
            success_count += 1
            
    print(f"\nNormalization complete! Successfully normalized {success_count}/{len(files)} files.")

if __name__ == "__main__":
    main()

