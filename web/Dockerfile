FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Set environment variables
ENV NEXT_PUBLIC_API_URL=http://32.192.3.27:8000
ENV NEXT_PUBLIC_APP_URL=http://32.192.3.27:3000

# Expose port
EXPOSE 3000

# Start the app in dev mode (faster, avoids static generation issues)
CMD ["npm", "run", "dev"]
