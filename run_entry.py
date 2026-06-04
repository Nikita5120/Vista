from pipeline.detect import StoreDetector

detector = StoreDetector()

detector.process_video(
    video_path=r"data\Store 1\CAM 3 - entry.mp4",
    store_id="STORE_001",
    camera_id="CAM_3_ENTRY",
)