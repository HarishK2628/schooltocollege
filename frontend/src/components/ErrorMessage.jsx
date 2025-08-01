import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';

const ErrorMessage = ({ message, onRetry }) => {
  return (
    <Alert className="border-red-200 bg-red-50">
      <AlertCircle className="h-4 w-4 text-red-600" />
      <AlertDescription className="text-red-800">
        <div className="flex items-center justify-between">
          <span>{message}</span>
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-red-600 hover:text-red-800 font-medium text-sm underline ml-4"
            >
              Try Again
            </button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
};

export default ErrorMessage;