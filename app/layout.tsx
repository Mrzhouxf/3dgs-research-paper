import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import './product.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'GS Observatory · 3DGS 渲染加速论文观察站',
  description: '追踪顶级会议中的 3D Gaussian Splatting 渲染加速研究。',
  openGraph: {title:'GS Observatory',description:'3DGS Rendering Research',images:['https://gs-rendering-observatory.gyvideo.chatgpt.site/og.png']},
  twitter: {card:'summary_large_image',title:'GS Observatory',images:['https://gs-rendering-observatory.gyvideo.chatgpt.site/og.png']},
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
