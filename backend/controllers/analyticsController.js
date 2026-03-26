const { runML } = require("../services/mlService");

exports.analyze = async (req, res) => {
    try {
        const result = await runML(req.body);
        res.json(result);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};