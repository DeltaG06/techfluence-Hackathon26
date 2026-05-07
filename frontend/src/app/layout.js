import { Montserrat } from 'next/font/google';
import './globals.css';

const montserrat = Montserrat({ subsets: ['latin'], display: 'swap', weight: ['400', '500', '600', '700'] });

export const metadata = {
  title: 'AuditAI — Financial Anomaly Detection',
  description: 'Real-time AI-powered financial anomaly detection and audit reporting dashboard.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className={`${montserrat.className} antialiased`}>
        {children}
      </body>
    </html>
  );
}
