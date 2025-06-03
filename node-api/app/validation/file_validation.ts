import { body } from 'express-validator';

export const validateFileUpload = [
  body().custom((_, { req }) => {
    const file = req.file;

    if (!file) {
      throw new Error('File is required');
    }

    const allowedMimeTypes = [
      'application/pdf',
      'application/msword', // .doc
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
    ];

    if (!allowedMimeTypes.includes(file.mimetype)) {
      throw new Error('Only PDF and Word files are allowed');
    }

    if (file.size > 5 * 1024 * 1024) {
      throw new Error('File size must be under 5MB');
    }

    return true;
  }),
];
