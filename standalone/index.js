const express = require('express')
const path = require('path');

const app = express()

const port = 3000

app.use(express.static('public'))

app.listen(port, () => {
    console.log(`Standalone Annotator listeining on port ${port}`)
})