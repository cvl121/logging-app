import Link from 'next/link';
import { useRouter } from 'next/router';

const Navbar = () => {
  const router = useRouter();

  const isActive = (path: string) => {
    return router.pathname === path ? 'bg-blue-700' : '';
  };

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="text-2xl font-bold">
            Logs Dashboard
          </Link>
          <div className="flex space-x-4">
            <Link
              href="/"
              className={`px-4 py-2 rounded hover:bg-blue-700 transition ${isActive('/')}`}
            >
              Dashboard
            </Link>
            <Link
              href="/logs"
              className={`px-4 py-2 rounded hover:bg-blue-700 transition ${isActive('/logs')}`}
            >
              Logs
            </Link>
            <Link
              href="/logs/create"
              className={`px-4 py-2 rounded hover:bg-blue-700 transition ${isActive('/logs/create')}`}
            >
              Create Log
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
