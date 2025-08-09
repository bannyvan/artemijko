FROM node:20-alpine

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9.7.1 --activate

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || pnpm install

COPY . .

EXPOSE 5173
CMD ["pnpm", "dev", "--host", "0.0.0.0"]