import NextAuth from "next-auth";
// import { authOptions } from "@/lib/auth"; (needs manual conversion)

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
