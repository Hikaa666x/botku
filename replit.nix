{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.flask  # Tambahkan Flask
    pkgs.python310Packages.yt-dlp
    pkgs.ffmpeg
  ];
}
