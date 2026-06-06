"use client";

interface DrillVideoEmbedProps {
  videoUrl: string;
  title?: string;
  className?: string;
}

function toEmbedUrl(url: string): string {
  if (url.includes("youtube.com/embed/")) return url;
  const watchMatch = url.match(/[?&]v=([\w-]{11})/);
  if (watchMatch) return `https://www.youtube.com/embed/${watchMatch[1]}`;
  const shortMatch = url.match(/youtu\.be\/([\w-]{11})/);
  if (shortMatch) return `https://www.youtube.com/embed/${shortMatch[1]}`;
  if (/^[\w-]{11}$/.test(url)) return `https://www.youtube.com/embed/${url}`;
  return url;
}

export function DrillVideoEmbed({ videoUrl, title, className }: DrillVideoEmbedProps) {
  const isYoutube =
    videoUrl.includes("youtube.com") ||
    videoUrl.includes("youtu.be") ||
    /^[\w-]{11}$/.test(videoUrl);

  if (isYoutube) {
    const embed = toEmbedUrl(videoUrl);
    return (
      <div className={className}>
        {title && (
          <p className="mb-2 text-sm font-medium text-[var(--color-foreground)]">{title}</p>
        )}
        <div className="relative aspect-video overflow-hidden rounded-xl border border-[var(--color-border)] bg-black">
          <iframe
            src={`${embed}?rel=0&modestbranding=1`}
            title={title ?? "Drill demonstration"}
            className="absolute inset-0 h-full w-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      {title && (
        <p className="mb-2 text-sm font-medium text-[var(--color-foreground)]">{title}</p>
      )}
      <div className="overflow-hidden rounded-xl border border-[var(--color-border)] bg-black">
        <video
          src={videoUrl}
          controls
          playsInline
          className="aspect-video w-full"
          preload="metadata"
        >
          Your browser does not support video playback.
        </video>
      </div>
    </div>
  );
}
