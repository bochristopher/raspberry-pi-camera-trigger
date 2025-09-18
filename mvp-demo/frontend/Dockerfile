FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# For development, use dev server
# For production, serve the built files
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]