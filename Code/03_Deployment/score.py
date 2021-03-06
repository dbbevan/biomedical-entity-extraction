import os
import numpy as np
import logging, sys, json
import timeit as t
from keras.models import load_model
from DataReader import DataReader
from EntityExtractor import EntityExtractor
import h5py

logger = logging.getLogger("stmt_logger")
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


def init():
    """ Initialise SD model
    """
    global entityExtractor

    start = t.default_timer()
    
    home_dir = os.getcwd() 
    print("home_dir = {}".format(home_dir))

    # define the word2vec embedding model hyperparameters
    window_size = 5
    vector_size = 50
    min_count =400
    #download_embedding_parquet_files_from_storage()
    #embedding_pickle_file = save_embeddings_to_pickle_file()
    
    embedding_pickle_file = os.path.join(home_dir, "w2vmodel_pubmed_vs_{}_ws_{}_mc_{}.pkl" \
            .format(vector_size, window_size, min_count))
    if not os.path.exists(embedding_pickle_file):
        print("The word embeddings pickle file ({}) doesn't exist.".format(embedding_pickle_file))

    tag_to_idx_map_file = os.path.join(home_dir,"tag_map.tsv")    
    if not os.path.exists(tag_to_idx_map_file):
        print("The entity types index mapping file ({}) doesn't exist.".format(tag_to_idx_map_file))

    # define the LSTM model hyperparameters
    network_type= 'unidirectional'
    # network_type= 'bidirectional'
    
    num_classes = 7 + 1
    max_seq_length = 613
    num_layers = 2
    num_hidden_units = 300
    num_epochs = 10

    model_file_path = os.path.join(home_dir,'Models','lstm_{}_model_units_{}_lyrs_{}_epchs_{}_vs_{}_ws_{}_mc_{}.h5'.\
                  format(network_type, num_hidden_units, num_layers,  num_epochs, embed_vector_size, window_size, min_count))
    
    if not os.path.exists(model_file_path):
        print("The neural model file ({}) doesn't exist.".format(model_file_path))

    print("Starting the model prediction ...")
    reader = DataReader(num_classes, max_seq_length=max_seq_length, tag_to_idx_map_file=tag_to_idx_map_file, vector_size =vector_size) 
    entityExtractor = EntityExtractor(reader, embedding_pickle_file)
    
    # Load model and load the model from brainscript (3rd index)
    try:
         #load the model
         print("Loading the entity extraction model {}".format(model_file_path))
         entityExtractor.load(model_file_path)
         entityExtractor.print_summary()     
    except:
        print("can't load the entity extraction model")
        pass
    end = t.default_timer()

    loadTimeMsg = "Model loading time: {0} ms".format(round((end-start)*1000, 2))
    logger.info(loadTimeMsg)

    
def run(input_df):
    """ Classify the input using the loaded model
    """
    import json

    global entityExtractor
    start = t.default_timer()

    # Generate Predictions
    pred = entityExtractor.predict_1(list(input_df["text"]))
    
    end = t.default_timer()

    logger.info("Entity extraciton took {0} ms".format(round((end-start)*1000, 2)))
        
    return json.dumps(pred)

def main():
  from azureml.api.schema.dataTypes import DataTypes
  from azureml.api.schema.sampleDefinition import SampleDefinition
  from azureml.api.realtime.services import generate_schema
  import pandas
  
  df = pandas.DataFrame(data=[['text-value']], columns=['text'])
  text_data = {}
  text_data['text'] = []
  text_data['text'].append(str('Famotidine is a histamine H2-receptor antagonist used in inpatient settings for prevention of stress ulcers.'))
  text_data['text'].append(str('Insulin is used to treat diabetes.'))

  input1 = pandas.DataFrame.from_dict(text_data)

  # Test the functions' output
  init()  
  print("Result: " + run(input1))
  
  inputs = {"input_df": SampleDefinition(DataTypes.PANDAS, df)}
  # The prepare statement writes the scoring file (main.py) and
  # the schema file (service_schema.json) the the output folder.
  generate_schema(run_func=run, inputs=inputs, filepath='service_schema.json')
  print("Schema generated")


if __name__ == "__main__":
    main()
