"use client";

import { RegisterForm } from "@/components/authentication/register-form";
import Image from "next/image";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";

export default function Register() {
  return <Suspense fallback={<p>Loading registration…</p>}><Registration /></Suspense>;
}

function Registration() {
  const [seed, setSeed] = useState<number | null>(null);
  const searchParams = useSearchParams();

  // Se não vier nada, cai por defeito para o dashboard
  const next = searchParams.get("next") || "/dashboard";

  useEffect(() => {
    setSeed(Math.floor(Math.random() * 100));
  }, []);



  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-muted p-6 md:p-10">
      {seed !== null && (
        <Image
          src={`https://picsum.photos/seed/${seed}/1920/1080`}
          height={1000}
          width={1000}
          className="absolute left-0 top-0 h-screen w-screen object-cover"
          alt="Cover"
        />
      )}
      <div className="absolute left-0 top-0 h-screen w-screen bg-white bg-opacity-50 dark:bg-black backdrop-blur-sm" />
      <div className="w-full max-w-sm md:max-w-3xl z-10">
        <RegisterForm next={next} />
      </div>
    </div>
  );
}
