import i18next from 'i18next'

export function initI18n() {
  if (i18next.isInitialized) return i18next
  i18next.init({
    lng: 'ru',
    fallbackLng: 'en',
    resources: {
      ru: { translation: { start: 'Старт', pause: 'Пауза', resume: 'Продолжить', finish: 'Завершить' } },
      en: { translation: { start: 'Start', pause: 'Pause', resume: 'Resume', finish: 'Finish' } }
    }
  })
  return i18next
}