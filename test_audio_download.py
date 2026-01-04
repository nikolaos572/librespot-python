#!/usr/bin/env python3
"""
Test script to download audio from Spotify using librespot-python
This script will attempt to download track 3QmLC9gCWbqvn7cUKWivq1

Usage:
  # With stored credentials:
  python test_audio_download.py /path/to/credentials.json
  
  # With OAuth (opens browser):
  python test_audio_download.py
"""

import logging
import sys
import os
from librespot.core import Session
from librespot.metadata import TrackId
from librespot.audio.decoders import AudioQuality, VorbisOnlyAudioQuality
from librespot import Version

# Configuration
# Set this to your credentials.json path, or pass as command line argument
CREDENTIALS_PATH = None  # e.g., "/path/to/credentials.json"

# Enable debug logging to see detailed information
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    # Display version information
    logger.info("=" * 80)
    logger.info("librespot-python Test Script")
    logger.info("=" * 80)
    logger.info(f"Version name: {Version.version_name}")
    logger.info(f"Version string: {Version.version_string()}")
    logger.info(f"System info: {Version.system_info_string()}")
    logger.info(f"Build info version: {Version.standard_build_info().version}")
    logger.info("=" * 80)
    
    # Determine credentials path from command line or config
    credentials_path = None
    if len(sys.argv) > 1:
        credentials_path = sys.argv[1]
    elif CREDENTIALS_PATH:
        credentials_path = CREDENTIALS_PATH
    
    # Create session
    try:
        if credentials_path and os.path.exists(credentials_path):
            logger.info(f"Creating session with stored credentials from: {credentials_path}")
            logger.info("Credentials format supported: Python librespot (username/type/credentials) or Rust librespot (username/auth_type/auth_data)")
            session = Session.Builder() \
                .stored_file(credentials_path) \
                .create()
            logger.info("✓ Session created successfully with stored credentials")
        else:
            if credentials_path:
                logger.warning(f"Credentials file not found: {credentials_path}")
            logger.info("Creating session with OAuth authentication...")
            logger.info("A browser window will open for authentication")
            session = Session.Builder() \
                .oauth(None) \
                .create()
            logger.info("✓ Session created successfully with OAuth")
    except Exception as e:
        logger.error(f"✗ Failed to create session: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Track ID to download
    track_uri = "spotify:track:3QmLC9gCWbqvn7cUKWivq1"
    logger.info(f"Track URI: {track_uri}")
    
    try:
        # Convert URI to TrackId
        track_id = TrackId.from_uri(track_uri)
        logger.info(f"✓ Track ID created: {track_id.hex_id()}")
    except Exception as e:
        logger.error(f"✗ Failed to parse track URI: {e}")
        sys.exit(1)
    
    try:
        # Get track metadata to see available files
        logger.info("Fetching track metadata...")
        track_metadata = session.api().get_metadata_4_track(track_id)
        
        logger.info("=" * 80)
        logger.info("Track Information:")
        logger.info(f"  Name: {track_metadata.name}")
        if track_metadata.artist:
            logger.info(f"  Artists: {', '.join([a.name for a in track_metadata.artist])}")
        if track_metadata.album:
            logger.info(f"  Album: {track_metadata.album.name}")
        logger.info(f"  Duration: {track_metadata.duration}ms")
        logger.info("=" * 80)
        
        # List all available audio files
        logger.info("Available audio files:")
        if not track_metadata.file:
            logger.error("✗ No audio files available for this track!")
            sys.exit(1)
        
        # Import Format enum for display
        from librespot.proto import Metadata_pb2 as Metadata
        format_names = {
            0: "OGG_VORBIS_96",
            1: "OGG_VORBIS_160", 
            2: "OGG_VORBIS_320",
            3: "MP3_256",
            4: "MP3_320",
            5: "MP3_160",
            6: "MP3_96",
            7: "MP3_160_ENC",
            8: "AAC_24",
            9: "AAC_48",
            16: "FLAC_FLAC",
            22: "FLAC_FLAC_24BIT"
        }
        
        for idx, audio_file in enumerate(track_metadata.file):
            format_name = format_names.get(audio_file.format, f"UNKNOWN({audio_file.format})")
            file_id_hex = audio_file.file_id.hex()
            logger.info(f"  [{idx}] Format: {format_name}, File ID: {file_id_hex}")
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"✗ Failed to fetch track metadata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    try:
        # Load the audio stream with highest quality
        logger.info("Loading audio stream (VERY_HIGH quality - OGG Vorbis 320kbps)...")
        quality_picker = VorbisOnlyAudioQuality(AudioQuality.VERY_HIGH)
        
        stream = session.content_feeder().load(
            track_id,
            quality_picker,
            False,  # preload
            None    # halt_listener
        )
        
        logger.info("✓ Audio stream loaded successfully!")
        logger.info("=" * 80)
        logger.info("Stream Information:")
        logger.info(f"  Codec: {stream.input_stream.codec()}")
        logger.info(f"  File ID: {stream.metrics.file_id}")
        logger.info(f"  Audio key fetch time: {stream.metrics.audio_key_time}ms")
        logger.info(f"  Preloaded: {stream.metrics.preloaded_audio_key}")
        logger.info("=" * 80)
        
        # Download the audio
        output_file = f"track_{track_id.hex_id()}.ogg"
        logger.info(f"Downloading audio to: {output_file}")
        
        with open(output_file, 'wb') as f:
            # Read the entire stream
            chunk_size = 1024 * 128  # 128KB chunks
            total_bytes = 0
            
            while True:
                try:
                    data = stream.input_stream.stream().read(chunk_size)
                    if not data:
                        break
                    f.write(data)
                    total_bytes += len(data)
                    
                    # Log progress every 1MB
                    if total_bytes % (1024 * 1024) == 0:
                        logger.info(f"  Downloaded: {total_bytes / (1024*1024):.1f}MB")
                        
                except Exception as e:
                    logger.error(f"Error during download: {e}")
                    break
        
        logger.info(f"✓ Download complete! Total size: {total_bytes / (1024*1024):.2f}MB")
        logger.info(f"✓ File saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"✗ Failed to load or download audio stream: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
