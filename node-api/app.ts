import express from 'express';
import bodyParser from 'body-parser';
import apis from './routes/routes';

const app = express();
const port = 5000;

app.use(bodyParser.json());

app.use('/', apis);

app.listen(port, () => {
  console.log(`Server connected on port ${port}`);
});
